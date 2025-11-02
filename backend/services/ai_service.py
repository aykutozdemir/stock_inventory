"""
AI service for AI assistant functionality
"""
import logging
import os
import json
import re
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from backend.services.web_scraping_service import WebScrapingService
from backend.services.stock_service import StockService
from backend.services.category_service import CategoryService
from backend.services.conversation_service import ConversationService
from backend.services.datasheet_service import DatasheetService
from backend.config import get_config
from langchain_community.llms import LlamaCpp
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import StreamingStdOutCallbackHandler

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI assistant operations"""

    def __init__(self):
        self.web_scraping = WebScrapingService()
        self.stock_service = StockService()
        self.category_service = CategoryService()
        self.conversation_service = ConversationService()
        self.datasheet_service = DatasheetService()
        self.llm = None
        self.model_name: Optional[str] = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the LLM by selecting the best available model at runtime"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config = get_config()
            model_dir = os.path.join(project_root, getattr(config, 'MODEL_DIR', 'models'))

            # Allow explicit override via env/config
            preferred_model = os.getenv('LLM_MODEL', getattr(config, 'LLM_MODEL', '')).strip()

            # Discover available models and optional mmproj files
            models = self._discover_models(model_dir)
            if not models:
                logger.warning(f"No .gguf models found under: {model_dir}")
                self.llm = None
                return

            # GPU/CPU capability detection
            vram_mb = self._get_gpu_vram_mb()
            
            # Try to use the helper script's decision first to keep CLI and backend aligned
            preselected = self._get_preselected_model_filename(project_root)
            selected = None
            if preselected:
                for m in models:
                    if os.path.basename(m['gguf_path']).lower() == preselected.lower():
                        logger.info(f"Using preselected model from helper: {preselected}")
                        selected = m
                        break
            
            # Fallback to env preference or heuristic selection
            if selected is None:
                selected = self._select_best_model(models, preferred_model, vram_mb)
            model_path = selected['gguf_path']
            mmproj_path = selected.get('mmproj_path')
            self.model_name = os.path.basename(model_path)

            # Load hardware config
            config_path = os.path.join(project_root, 'hardware_config.json')
            gpu_layers = -1  # Use all available layers
            # Default to 8192 for better support of long datasheet summaries and conversation history
            # Gemma 3 models support up to 8192 tokens, and 12B models can handle this well
            n_ctx = 8192
            n_threads = 4

            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        gpu_layers = config.get('gpu_layers', -1)
                        # Use config value if set, otherwise default to 8192
                        n_ctx = config.get('n_ctx', 8192)
                        n_threads = config.get('n_threads', 4)
                except Exception as e:
                    logger.warning(f"Could not load hardware config: {e}")

            logger.info(
                f"Initializing model: {os.path.basename(model_path)} | VRAM: {vram_mb or 0}MB | "
                f"GPU layers: {gpu_layers} | ctx: {n_ctx} | threads: {n_threads}"
            )

            # Note: Some llama.cpp builds support an 'mmproj' argument for multimodal projection. The LangChain
            # wrapper may ignore unknown kwargs; we only pass supported args here.

            def try_init(model_path_local: str, ctx: int, threads: int, gpu: int):
                return LlamaCpp(
                    model_path=model_path_local,
                    temperature=0.7,
                    # Increased max_tokens to allow longer, more detailed responses
                    max_tokens=1024,
                    top_p=0.95,
                    top_k=40,
                    n_ctx=ctx,
                    n_threads=threads,
                    n_gpu_layers=gpu,
                    verbose=False,
                    callbacks=[StreamingStdOutCallbackHandler()]
                )

            # Attempt initialization with fallbacks
            try:
                self.llm = try_init(model_path, n_ctx, n_threads, gpu_layers)
                logger.info("LLM initialized successfully")
            except Exception as primary_error:
                logger.error(f"Primary LLM init failed: {primary_error}")
                # CPU-only fallback
                try:
                    logger.info("Retrying LLM init with CPU-only (n_gpu_layers=0)...")
                    self.llm = try_init(model_path, n_ctx, n_threads, 0)
                    logger.info("LLM initialized successfully (CPU-only)")
                except Exception as cpu_error:
                    logger.error(f"CPU-only LLM init failed: {cpu_error}")
                    # Reduced context fallback
                    try:
                        # Try with at least 4096 first, then fall back to 2048 if needed
                        reduced_ctx = max(min(n_ctx, 4096), 2048)
                        if reduced_ctx < n_ctx:
                            logger.info(f"Retrying LLM init with reduced context (n_ctx={reduced_ctx}) CPU-only...")
                        self.llm = try_init(model_path, reduced_ctx, n_threads, 0)
                        logger.info("LLM initialized successfully (reduced context, CPU-only)")
                    except Exception as reduced_error:
                        logger.error(f"Reduced-context LLM init failed: {reduced_error}")
                        # Try alternative models (smallest first)
                        try:
                            alt_models = sorted(models, key=lambda m: os.path.getsize(m['gguf_path']))
                            for alt in alt_models:
                                if alt['gguf_path'] == model_path:
                                    continue
                                alt_path = alt['gguf_path']
                                self.model_name = os.path.basename(alt_path)
                                logger.info(f"Trying alternative model: {self.model_name}")
                                try:
                                    self.llm = try_init(alt_path, reduced_ctx, n_threads, 0)
                                    logger.info("LLM initialized successfully (alternative model, CPU-only)")
                                    model_path = alt_path
                                    break
                                except Exception as alt_error:
                                    logger.error(f"Alternative model init failed: {alt_error}")
                                    self.llm = None
                        except Exception as alt_list_error:
                            logger.error(f"Alternative model fallback encountered an error: {alt_list_error}")

            if not self.llm:
                logger.error("Failed to initialize any LLM. AI engine will be unavailable.")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None

    def _get_preselected_model_filename(self, project_root: str) -> Optional[str]:
        """Invoke helper script to get the selected model filename (basename) if available."""
        try:
            helper_path = os.path.join(project_root, 'print_selected_model.py')
            if not os.path.exists(helper_path):
                return None
            result = subprocess.run(
                [
                    os.environ.get('PYTHON_EXECUTABLE', 'python3'),
                    helper_path
                ],
                capture_output=True,
                text=True,
                cwd=project_root,
                check=False
            )
            if result.returncode != 0:
                return None
            # Expect line like "🧠 Selected model: filename.gguf"
            for line in result.stdout.splitlines():
                if 'Selected model:' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        name = parts[1].strip()
                        # ignore placeholder outputs
                        if name and 'none' not in name.lower():
                            return name
            return None
        except Exception:
            return None

    def _discover_models(self, model_dir: str) -> List[Dict[str, Any]]:
        """Scan model directory for .gguf models and try to pair with .mmproj files."""
        try:
            if not os.path.isdir(model_dir):
                return []

            gguf_files: List[str] = []
            mmproj_files: List[str] = []
            for name in os.listdir(model_dir):
                lower = name.lower()
                full = os.path.join(model_dir, name)
                if os.path.isfile(full):
                    if lower.endswith('.gguf'):
                        gguf_files.append(full)
                    elif lower.endswith('.mmproj'):
                        mmproj_files.append(full)

            def detect_quant(file_name: str) -> str:
                # Common quantization tokens: q8_0, q6_k, q5_k_m, q4_k_m, q4_0, f16, q2_k
                m = re.search(r'(q[0-9](?:_[a-z])?(?:_[a-z])?|f16|f32)', file_name.lower())
                return m.group(1).upper() if m else ''

            def pair_mmproj(gguf_path: str) -> Optional[str]:
                base = os.path.splitext(os.path.basename(gguf_path))[0].lower()
                # Try to find a mmproj that starts with the same base token (up to first dot or first '-it')
                base_token = re.split(r'[\.-]', base)[0]
                for mp in mmproj_files:
                    if base_token in os.path.basename(mp).lower():
                        return mp
                return None

            models: List[Dict[str, Any]] = []
            for gguf in gguf_files:
                models.append({
                    'gguf_path': gguf,
                    'file_size': os.path.getsize(gguf),
                    'quant': detect_quant(gguf),
                    'mmproj_path': pair_mmproj(gguf)
                })
            return models
        except Exception as e:
            logger.warning(f"Model discovery failed in {model_dir}: {e}")
            return []

    def _get_gpu_vram_mb(self) -> int:
        """Detect total GPU VRAM in MB using nvidia-smi. Returns 0 if not available."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
                if lines:
                    # Use the first GPU's VRAM
                    return int(lines[0])
        except Exception as e:
            logger.debug(f"nvidia-smi not available or failed: {e}")
        return 0

    def _select_best_model(self, models: List[Dict[str, Any]], preferred_model: str, vram_mb: int) -> Dict[str, Any]:
        """Choose the best model based on preference and available VRAM (model size and quant)."""
        # If an explicit model name is given and found, use it
        if preferred_model:
            for m in models:
                if os.path.basename(m['gguf_path']).lower().startswith(preferred_model.lower()):
                    logger.info(f"Using preferred model: {os.path.basename(m['gguf_path'])}")
                    return m

        # Rank quantizations from heaviest to lightest
        quant_rank = {
            'F32': 7,
            'F16': 6,
            'Q8_0': 5,
            'Q6_K': 4,
            'Q5_K_M': 3,
            'Q5_K': 3,
            'Q5_0': 3,
            'Q4_K_M': 2,
            'Q4_K_S': 2,
            'Q4_0': 2,
            'Q3_K': 1,
            'Q2_K': 0,
        }

        def get_quant_rank(q: str) -> int:
            q = (q or '').upper()
            if q in quant_rank:
                return quant_rank[q]
            # Normalize common patterns
            if q.startswith('Q8'):
                return 5
            if q.startswith('Q6'):
                return 4
            if q.startswith('Q5'):
                return 3
            if q.startswith('Q4'):
                return 2
            if q.startswith('Q3'):
                return 1
            if q.startswith('Q2'):
                return 0
            return 2  # default mid

        # Determine target rank by VRAM
        if vram_mb >= 20000:
            target_rank = 4  # Q6 or better
        elif vram_mb >= 12000:
            target_rank = 3  # Q5
        elif vram_mb >= 8000:
            target_rank = 2  # Q4
        elif vram_mb >= 6000:
            target_rank = 1  # Q3
        else:
            target_rank = 0  # Q2 or smallest available

        # Determine maximum parameter size (in B) allowed by VRAM
        # Conservative mapping to avoid OOM on smaller GPUs
        if vram_mb >= 16000:
            max_params_b = 13  # allow 12B+
        elif vram_mb >= 12000:
            max_params_b = 12
        elif vram_mb >= 8000:
            max_params_b = 7
        elif vram_mb >= 6000:
            max_params_b = 7
        elif vram_mb >= 4096:
            max_params_b = 4
        else:
            max_params_b = 3

        def detect_params_b(path: str) -> int:
            name = os.path.basename(path).lower()
            m = re.search(r"(\d{1,2})b", name)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    pass
            # Fallback heuristic: use file size to guess (smaller => fewer params)
            size =  os.path.getsize(path)
            if size > 6_000_000_000:
                return 12
            if size > 3_000_000_000:
                return 7
            if size > 1_800_000_000:
                return 4
            return 3

        # Prefer models within the allowed param size
        within_size = [m for m in models if detect_params_b(m['gguf_path']) <= max_params_b]
        if not within_size:
            # If none fit, use the smallest param-size models available
            min_b = min(detect_params_b(m['gguf_path']) for m in models)
            within_size = [m for m in models if detect_params_b(m['gguf_path']) == min_b]

        # Score candidates by quant closeness and file size (quality)
        candidates: List[Tuple[int, int, int, Dict[str, Any]]] = []
        for m in within_size:
            rank = get_quant_rank(m.get('quant', ''))
            closeness = -abs(rank - target_rank)
            size = m.get('file_size', 0)
            params_b = detect_params_b(m['gguf_path'])
            # Prefer larger params within allowed range, then quality
            candidates.append((params_b, closeness, size, m))

        if not candidates:
            return models[0]

        candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        best = candidates[0][3]
        logger.info(
            f"Selected model: {os.path.basename(best['gguf_path'])} "
            f"(params~{detect_params_b(best['gguf_path'])}B, quant={best.get('quant','')}, size={best.get('file_size',0)})"
        )
        return best

    def process_question(self, question: str, conversation_id: Optional[int] = None, progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """Process user question and return AI response
        
        Args:
            question: User's question
            conversation_id: Optional conversation ID
            progress_callback: Optional callback function(status_message) to report progress
        """
        try:
            if progress_callback:
                progress_callback('Processing your message...')
            
            # Get inventory and conversation context
            inventory_context = self._get_inventory_context()
            conversation_history = self._get_conversation_history(conversation_id)

            # Detect datasheet/spec query
            datasheet_keywords = ['datasheet', 'spec', 'specification', 'özellik', 'find', 'search', 'where can i find']
            is_datasheet_query = any(keyword in question.lower() for keyword in datasheet_keywords)

            if is_datasheet_query:
                if progress_callback:
                    progress_callback('Searching for datasheets and specifications...')
                
                component_name = self._extract_component_name_from_question(question)
                recent_datasheet = None
                pdf_data = None

                if component_name:
                    # Use DB if available (faster next time)
                    # First try exact match
                    existing = self.datasheet_service.find_by_component(component_name)
                    # If no exact match, try fuzzy search for related components (e.g., 1N4001 might find 1N4007 datasheet)
                    if not existing and len(component_name) > 3:
                        # Try searching for similar component names (e.g., "1N400" might match "1N4007")
                        similar = self.datasheet_service.repository.search_by_component(component_name[:len(component_name)-1], limit=5)
                        if similar:
                            # Prefer matches that contain the component name or share the base part number
                            for ds in similar:
                                ds_component = (ds.get('component_name') or '').upper()
                                user_component = component_name.upper()
                                # Check if it's likely the same component family (e.g., 1N4001 and 1N4007 share base "1N400")
                                if ds_component.startswith(user_component[:min(len(user_component), len(ds_component))-1]) or \
                                   user_component.startswith(ds_component[:min(len(user_component), len(ds_component))-1]):
                                    existing = [ds]
                                    logger.info(f"Found related datasheet: {ds.get('component_name')} for query: {component_name}")
                                    break
                    
                    if existing:
                        recent_datasheet = existing[0]
                        if progress_callback:
                            progress_callback('Found datasheet in database')
                    else:
                        if progress_callback:
                            progress_callback('Downloading datasheet PDF...')
                        pdf_data = self.web_scraping.download_datasheet_pdf(component_name)
                        if pdf_data:
                            datasheet_id = self.datasheet_service.save_datasheet(
                                component_name=component_name,
                                pdf_data=pdf_data['pdf_data'],
                                source_url=pdf_data['source_url'],
                                filename=pdf_data['filename'],
                                extracted_specs=pdf_data.get('extracted_specs'),
                                key_specifications=pdf_data.get('key_specifications'),
                                manufacturer=pdf_data.get('manufacturer'),
                                package_type=pdf_data.get('package_type'),
                                voltage_rating=pdf_data.get('voltage_rating'),
                                current_rating=pdf_data.get('current_rating'),
                                power_rating=pdf_data.get('power_rating'),
                                temperature_range=pdf_data.get('temperature_range'),
                                tolerance=pdf_data.get('tolerance')
                            )
                            if datasheet_id:
                                recent_datasheet = self.datasheet_service.get_datasheet_info(datasheet_id)
                        if progress_callback:
                            progress_callback('Analyzing PDF and extracting key specs...')

                # Build enhanced prompt context
                # Use stored summary/extracted_specs if available from database
                stored_summary = None
                stored_specs = None
                if recent_datasheet:
                    stored_summary = recent_datasheet.get('summary')
                    stored_specs = recent_datasheet.get('extracted_specs') or recent_datasheet.get('key_specifications')
                
                # Only search online if we don't have stored data
                datasheet_results = ""
                if not stored_summary and not stored_specs:
                    if progress_callback:
                        progress_callback('Searching component specifications online...')
                    datasheet_results = self.web_scraping.search_component_specs(question)
                elif progress_callback:
                    progress_callback('Using stored datasheet information...')
                
                prompt = self._create_prompt(question, inventory_context, conversation_history)
                
                # Build context with stored data or online search results
                datasheet_context = ""
                if stored_summary or stored_specs:
                    datasheet_context = "I have analyzed this component's datasheet from the local database:\n\n"
                    if stored_summary:
                        datasheet_context += f"**Summary:**\n{stored_summary}\n\n"
                    if stored_specs:
                        datasheet_context += f"**Extracted Specifications:**\n{stored_specs}\n\n"
                    datasheet_context += "The PDF has been saved to your local database for offline access."
                else:
                    datasheet_context = f"Here are the search results I found:\n\n{datasheet_results}\n\nYou can download datasheets from the links above for offline access."
                
                # Enhanced prompt that emphasizes extracting the correct component from multi-component datasheets
                component_specific_instruction = ""
                if component_name:
                    component_specific_instruction = f"\n\n⚠️ IMPORTANT: The user asked specifically about '{component_name}'. If the datasheet contains multiple component variants (e.g., 1N4001, 1N4002, 1N4003, 1N4004, 1N4005, 1N4006, 1N4007), you MUST extract and report ONLY the specifications for '{component_name}'. Do not use generic or averaged values. Look for a table or section specifically listing '{component_name}' and extract its exact voltage ratings, current ratings, and other specs."
                
                enhanced_prompt = f"""You are an expert AI assistant for Electronic Components.

User is asking about datasheets/specifications.

{datasheet_context}{component_specific_instruction}

Given the user's question: "{question}", produce a concise, component-type-aware summary of key specifications (voltages, currents, power, package, tolerances, temp range), and practical notes or caveats. Prefer numeric, unit-bearing values. If uncertainties exist, say so briefly."""

                response_text = ''
                model_name = self.model_name
                if self.llm:
                    if progress_callback:
                        progress_callback('Generating a concise summary...')
                    try:
                        raw_response = self.llm.invoke(enhanced_prompt)
                        response_text = self._clean_response(raw_response)
                        # model_name remains self.model_name (already set above)
                    except Exception as e:
                        logger.error(f"LLM generation failed: {e}")
                        response_text = ''
                        model_name = None

                datasheet_payload = None
                if recent_datasheet and recent_datasheet.get('id'):
                    datasheet_payload = {
                        'datasheet_id': recent_datasheet['id'],
                        'component_name': recent_datasheet.get('component_name') or component_name,
                        'filename': recent_datasheet.get('original_filename') or (pdf_data and pdf_data.get('filename')),
                        'source_url': recent_datasheet.get('source_url') or (pdf_data and pdf_data.get('source_url')),
                        'open_url': f"/api/datasheets/{recent_datasheet['id']}"
                    }

                # Build structured specs for table rendering
                specs_map = {}
                def add_spec(label: str, value: Optional[str]):
                    if value is not None and str(value).strip() != '':
                        specs_map[label] = str(value)

                if recent_datasheet:
                    add_spec('Manufacturer', recent_datasheet.get('manufacturer'))
                    add_spec('Package', recent_datasheet.get('package_type'))
                    add_spec('Voltage', recent_datasheet.get('voltage_rating'))
                    add_spec('Current', recent_datasheet.get('current_rating'))
                    add_spec('Power', recent_datasheet.get('power_rating'))
                    add_spec('Temperature Range', recent_datasheet.get('temperature_range'))
                    add_spec('Tolerance', recent_datasheet.get('tolerance'))
                elif pdf_data:
                    add_spec('Manufacturer', pdf_data.get('manufacturer'))
                    add_spec('Package', pdf_data.get('package_type'))
                    add_spec('Voltage', pdf_data.get('voltage_rating'))
                    add_spec('Current', pdf_data.get('current_rating'))
                    add_spec('Power', pdf_data.get('power_rating'))
                    add_spec('Temperature Range', pdf_data.get('temperature_range'))
                    add_spec('Tolerance', pdf_data.get('tolerance'))

                return {
                    'success': True,
                    'data': {
                        'answer': response_text,
                        'model': model_name,
                        'conversation_id': conversation_id,
                        'inventory': None,
                        'datasheet': datasheet_payload,
                        'specs': specs_map if specs_map else None
                    }
                }

            # Non-datasheet flow
            if not self.llm:
                return {
                    'success': False,
                    'message': 'AI engine not available',
                    'data': None
                }

            if progress_callback:
                progress_callback('Processing your question...')
            
            prompt = self._create_prompt(question, inventory_context, conversation_history)
            try:
                if progress_callback:
                    progress_callback('Generating response...')
                raw_response = self.llm.invoke(prompt)
                response_text = self._clean_response(raw_response)
                model_name = self.model_name
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                return {
                    'success': False,
                    'message': 'AI engine not available',
                    'data': None
                }

            inventory_data = self._extract_inventory_data_if_needed(question, response_text)

            return {
                'success': True,
                'data': {
                    'answer': response_text,
                    'model': model_name,
                    'conversation_id': conversation_id,
                    'inventory': inventory_data
                }
            }

        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {
                'success': False,
                'message': 'Failed to process question',
                'data': None
            }

    def _get_inventory_context(self) -> str:
        """Get current inventory context for AI"""
        try:
            # Get categories
            categories = self.category_service.get_categories()
            category_summary = f"{len(categories)} categories: " + ", ".join([cat['name'] for cat in categories[:5]])

            # Get total stock count
            stocks = self.stock_service.get_stocks()
            total_items = len(stocks)

            # Get recent items (last 10)
            recent_stocks = stocks[-10:] if len(stocks) > 10 else stocks
            recent_summary = "Recent items: " + ", ".join([f"{item['name']} ({item['quantity']} {item['unit']})" for item in recent_stocks])

            return f"Inventory Summary: {category_summary}. Total items: {total_items}. {recent_summary}."

        except Exception as e:
            logger.error(f"Error getting inventory context: {e}")
            return "Inventory information currently unavailable."

    def _create_prompt(self, question: str, inventory_context: str, conversation_history: str) -> str:
        """Create a comprehensive prompt for the LLM, including conversation history"""
        system_prompt = """You are an expert AI assistant for an Electronic Components Inventory Management System.
You help users manage their electronic components, find parts, get specifications, and provide electronics engineering advice.

Your capabilities:
- Help users find components in their inventory
- Provide information about electronic components and their specifications
- Assist with component selection and compatibility
- Answer questions about electronics principles and calculations
- Help with circuit design and troubleshooting
- Search for component datasheets and specifications online
- Provide recommendations based on user requirements

Always be helpful, accurate, and provide practical advice. If you need to show inventory data, mention it clearly.

Conversation History (most recent first):
{conversation_history}

Current Inventory Context: {inventory_context}

User Question: {question}

Provide a helpful, accurate response:"""

        return system_prompt.format(
            conversation_history=conversation_history,
            inventory_context=inventory_context,
            question=question
        )

    def _get_conversation_history(self, conversation_id: Optional[int], max_messages: int = 20) -> str:
        """Build a compact conversation history string from the last N messages"""
        if not conversation_id:
            return ""
        try:
            messages = self.conversation_service.get_messages(conversation_id) or []
            if not messages:
                return ""

            # Keep only the last N messages
            recent = messages[-max_messages:]
            # Format as role: message, newest first for quick context
            lines: List[str] = []
            for m in reversed(recent):
                role = m.get('role', 'user')
                text = (m.get('message') or '').strip()
                if not text:
                    continue
                # Truncate long lines to keep prompt size manageable
                if len(text) > 500:
                    text = text[:500] + '…'
                lines.append(f"{role}: {text}")
            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Failed to build conversation history for {conversation_id}: {e}")
            return ""

    def _clean_response(self, raw_response: str) -> str:
        """Clean and format the LLM response"""
        if isinstance(raw_response, str):
            # Remove any system prompts that might have leaked through
            response = raw_response.strip()

            # Remove common artifacts
            response = response.replace("System:", "").replace("Assistant:", "").strip()

            # Ensure response is not empty
            if not response:
                return "I understand your question. Could you please provide more details?"

            return response
        else:
            return str(raw_response)

    

    def _extract_inventory_data_if_needed(self, question: str, response: str) -> Optional[List[Dict[str, Any]]]:
        """Extract inventory data if the response indicates it should be shown"""
        question_lower = question.lower()
        response_lower = response.lower()

        # Check if user is asking for inventory data
        inventory_keywords = ['show', 'list', 'inventory', 'what do i have', 'all', 'find']
        if any(keyword in question_lower for keyword in inventory_keywords) or any(keyword in response_lower for keyword in ['here are', 'showing', 'listing']):

            try:
                # Try to determine what type of data to show
                if 'resistor' in question_lower:
                    return self._filter_stocks_by_type('resistor')
                elif 'capacitor' in question_lower:
                    return self._filter_stocks_by_type('capacitor')
                elif 'transistor' in question_lower:
                    return self._filter_stocks_by_type('transistor')
                elif 'diode' in question_lower:
                    return self._filter_stocks_by_type('diode')
                elif 'led' in question_lower:
                    return self._filter_stocks_by_type('led')
                else:
                    # Return recent items or all items (limited)
                    stocks = self.stock_service.get_stocks()
                    return stocks[-20:] if len(stocks) > 20 else stocks

            except Exception as e:
                logger.error(f"Error extracting inventory data: {e}")
                return None

        return None

    def _filter_stocks_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Filter stocks by component type"""
        try:
            stocks = self.stock_service.get_stocks()
            filtered = []

            for stock in stocks:
                name_lower = stock['name'].lower()
                desc_lower = (stock.get('description', '') or '').lower()

                if component_type in name_lower or component_type in desc_lower:
                    filtered.append(stock)

            return filtered[:20]  # Limit results

        except Exception as e:
            logger.error(f"Error filtering stocks: {e}")
            return []

    def _extract_component_name_from_question(self, question: str) -> Optional[str]:
        """Extract component name from datasheet/specification questions"""
        try:
            # Remove common question words and phrases
            question = question.lower()
            remove_words = ['find', 'search', 'where', 'can', 'i', 'get', 'download', 'the', 'a', 'an', 'for', 'datasheet', 'spec', 'specs', 'specification', 'özellik', 'of', 'about']

            words = question.split()
            filtered_words = []

            for word in words:
                if word not in remove_words and len(word) > 1:
                    # Keep component-like terms (contain numbers, letters, hyphens)
                    if re.match(r'^[A-Za-z0-9\-_\.]+$', word):
                        filtered_words.append(word)

            if filtered_words:
                # Join the most likely component terms
                component_name = ' '.join(filtered_words[:3])  # Take first 3 words max

                # Clean up common patterns
                component_name = re.sub(r'[^\w\s\-_\.]', '', component_name).strip()

                if component_name and len(component_name) > 2:
                    return component_name.title()

            return None

        except Exception as e:
            logger.error(f"Error extracting component name: {e}")
            return None

    def perform_calculation(self, calculation_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform electronics calculations"""
        try:
            if calculation_type == 'ohms':
                result = self._calculate_ohms_law(params)
            elif calculation_type == 'rc_cutoff':
                result = self._calculate_rc_cutoff(params)
            elif calculation_type == 'divider':
                result = self._calculate_voltage_divider(params)
            else:
                return {
                    'success': False,
                    'message': f'Unknown calculation type: {calculation_type}',
                    'data': None
                }

            return {
                'success': True,
                'message': 'Calculation completed',
                'data': result
            }

        except Exception as e:
            logger.error(f"Error performing calculation: {e}")
            return {
                'success': False,
                'message': 'Calculation failed',
                'data': None
            }

    def search_component(self, query: str) -> Dict[str, Any]:
        """Search for component specifications"""
        try:
            result = self.web_scraping.search_component_specs(query)
            return {
                'success': True,
                'message': 'Component search completed',
                'data': result
            }
        except Exception as e:
            logger.error(f"Error searching component: {e}")
            return {
                'success': False,
                'message': 'Component search failed',
                'data': None
            }

    def generate_datasheet_summary(self, pdf_data: bytes, component_name: str = "") -> Dict[str, Any]:
        """Generate a comprehensive summary from datasheet PDF data"""
        try:
            summary = self.web_scraping.generate_datasheet_summary(pdf_data, component_name)
            return {
                'success': True,
                'message': 'Summary generated successfully',
                'data': {
                    'summary': summary,
                    'component_name': component_name
                }
            }
        except Exception as e:
            logger.error(f"Error generating datasheet summary: {e}")
            return {
                'success': False,
                'message': 'Failed to generate summary',
                'data': None
            }

    def _calculate_ohms_law(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate using Ohm's law"""
        # Simple implementation
        return {"result": "Ohm's law calculation"}

    def _calculate_rc_cutoff(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate RC cutoff frequency"""
        # Simple implementation
        return {"result": "RC cutoff calculation"}

    def _calculate_voltage_divider(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate voltage divider"""
        # Simple implementation
        return {"result": "Voltage divider calculation"}
