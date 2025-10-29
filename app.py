from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import json
import requests
import threading

# LangChain (local LLM via llama-cpp)
try:
    from langchain_community.llms import LlamaCpp
except Exception:
    LlamaCpp = None
try:
    from langchain.agents import initialize_agent, AgentType
    from langchain.tools import Tool
    from langchain.memory import ConversationBufferMemory
except Exception:
    initialize_agent = None
    AgentType = None
    Tool = None
    ConversationBufferMemory = None

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE = 'inventory.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
 

# Local model selection for LangChain
MODEL_DIR = os.getenv('MODEL_DIR', 'models')
LLM_MODEL = os.getenv('LLM_MODEL', '')  # absolute or relative path to .gguf

_LLM_INSTANCE = None
_LLM_LOCK = threading.Lock()
_AGENT_EXECUTOR = None
_AGENT_LOCK = threading.Lock()
_LLM_MODEL_NAME = None

MEMORY_DIR = os.path.join(os.getcwd(), 'memory')
os.makedirs(MEMORY_DIR, exist_ok=True)
MEMORY_FILE = os.path.join(MEMORY_DIR, 'agent_memory.json')

def _read_persistent_memory() -> dict:
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}

def _write_persistent_memory(data: dict) -> None:
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _find_local_model_path():
    if LLM_MODEL and os.path.exists(LLM_MODEL):
        return LLM_MODEL
    # Prefer small chat-friendly models first
    preferred = [
        'Phi-3.1-mini-4k-instruct', 'phi-3.1-mini-4k-instruct',
        'Phi-3-mini-4k-instruct', 'phi-3-mini-4k-instruct',
        'phi-3-medium-4k-instruct', 'Phi-3-medium-4k-instruct',
        'gemma-3-12b-it', 'gemma-2-9b-it', 'tinyllama'
    ]
    try:
        if os.path.isdir(MODEL_DIR):
            all_files = [os.path.join(MODEL_DIR, f) for f in os.listdir(MODEL_DIR) if f.lower().endswith('.gguf')]
            # Try preferred order
            for name in preferred:
                for fp in all_files:
                    if name.lower() in os.path.basename(fp).lower():
                        return fp
            # Fallback: first .gguf
            if all_files:
                return all_files[0]
    except Exception:
        pass
    return ''

def get_llm():
    global _LLM_INSTANCE
    global _LLM_MODEL_NAME
    if _LLM_INSTANCE is not None:
        return _LLM_INSTANCE
    if LlamaCpp is None:
        raise RuntimeError('LangChain LlamaCpp not available. Install requirements.')
    model_path = _find_local_model_path()
    if not model_path:
        raise RuntimeError('No local GGUF model found. Place a .gguf under models/ or set LLM_MODEL env var.')
    with _LLM_LOCK:
        if _LLM_INSTANCE is None:
            _LLM_INSTANCE = LlamaCpp(
                model_path=model_path,
                n_ctx=4096,
                temperature=0.3,
                n_threads=max(2, (os.cpu_count() or 4) // 2),
                f16_kv=True,
                n_gpu_layers=0
            )
            _LLM_MODEL_NAME = os.path.basename(model_path)
    return _LLM_INSTANCE

def get_llm_model_name() -> str:
    # Ensure LLM is initialized to know the path
    try:
        get_llm()
    except Exception:
        pass
    return _LLM_MODEL_NAME or ''

def _extract_inventory_rows_from_text(text: str):
    """Try to extract a JSON array of inventory rows from agent text.
    Returns a list of dicts with expected keys if found, else []."""
    import re
    if not isinstance(text, str) or '[' not in text or ']' not in text:
        return []
    candidates = []
    # Try fenced ```json blocks first
    try:
        for m in re.finditer(r"```json\s*(\[.*?\])\s*```", text, flags=re.DOTALL | re.IGNORECASE):
            candidates.append(m.group(1))
    except Exception:
        pass
    # Fallback: first bracketed array in text
    if not candidates:
        try:
            start = text.find('[')
            end = text.rfind(']')
            if 0 <= start < end:
                candidates.append(text[start:end+1])
        except Exception:
            pass
    for c in candidates:
        try:
            data = json.loads(c)
            if isinstance(data, list) and data and isinstance(data[0], dict):
                # minimal schema check
                sample = data[0]
                if any(k in sample for k in ('name','quantity','unit','category')):
                    return data
        except Exception:
            continue
    return []

def _tool_inventory_search(query: str) -> str:
    """Search inventory by name substring; returns up to 20 rows with quantities and categories."""
    q = (query or '').strip()
    conn = None
    try:
        conn = get_db_connection()
        if q:
            cursor = conn.execute(
                'SELECT s.name, s.quantity, s.unit, c.name as category FROM stocks s '
                'LEFT JOIN categories c ON s.category_id = c.id '
                'WHERE s.name LIKE ? ORDER BY s.name LIMIT 20', (f'%{q}%',)
            )
        else:
            cursor = conn.execute(
                'SELECT s.name, s.quantity, s.unit, c.name as category FROM stocks s '
                'LEFT JOIN categories c ON s.category_id = c.id '
                'ORDER BY s.name LIMIT 20'
            )
        rows = [dict(name=r[0], quantity=r[1], unit=r[2], category=r[3]) for r in cursor.fetchall()]
        return json.dumps(rows, ensure_ascii=False)
    except Exception as e:
        return f"error: {str(e)}"
    finally:
        if conn:
            conn.close()

def _tool_web_search(query: str) -> str:
    """Quick web search using DuckDuckGo Instant Answer; returns brief text lines."""
    try:
        url = "https://api.duckduckgo.com/"
        params = { 'q': query, 'format': 'json', 'no_html': '1', 'skip_disambig': '1' }
        r = requests.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return f"error: http {r.status_code}"
        d = r.json()
        out = []
        if d.get('Abstract'): out.append(f"Abstract: {d['Abstract']}")
        if d.get('AbstractText'): out.append(d['AbstractText'])
        if d.get('RelatedTopics'):
            for t in d['RelatedTopics'][:3]:
                if isinstance(t, dict) and t.get('Text'):
                    out.append(t['Text'][:220])
        return "\n".join(out) or "no results"
    except Exception as e:
        return f"error: {str(e)}"

def _parse_value(val: str) -> float:
    """Parse numeric with common SI suffixes: k, M, m, u, n."""
    s = val.strip().lower().replace('ohm', '').replace('Ω','').replace(' ','')
    mult = 1.0
    if s.endswith('k'): mult, s = 1e3, s[:-1]
    elif s.endswith('m') and not s.endswith('mm'): mult, s = 1e-3, s[:-1]
    elif s.endswith('u') or s.endswith('µ'): mult, s = 1e-6, s[:-1]
    elif s.endswith('n'): mult, s = 1e-9, s[:-1]
    elif s.endswith('meg'): mult, s = 1e6, s[:-3]
    elif s.endswith('g'): mult, s = 1e9, s[:-1]
    return float(s) * mult

def _tool_electronics_calc(cmd: str) -> str:
    """Electronics calculator. Supported:
    - ohms: provide any two of V, I, R (e.g., 'ohms V=5, R=2k')
    - rc_cutoff: 'rc_cutoff R=10k, C=100nF'
    - divider: 'divider Vin=5, R1=10k, R2=5k' (returns Vout)
    Fallback: evaluate arithmetic expression safely (e.g., '2.2k*3').
    """
    import math
    t = (cmd or '').strip().lower()
    try:
        if t.startswith('ohms'):
            parts = dict([p.strip().split('=') for p in t.split(' ',1)[1].split(',') if '=' in p]) if ' ' in t else {}
            V = parts.get('v'); I = parts.get('i'); R = parts.get('r')
            Vv = _parse_value(V) if V else None
            Ii = _parse_value(I) if I else None
            Rr = _parse_value(R) if R else None
            if Vv is None and Ii is not None and Rr is not None: Vv = Ii*Rr
            if Ii is None and Vv is not None and Rr is not None: Ii = Vv/Rr
            if Rr is None and Vv is not None and Ii is not None: Rr = Vv/Ii
            return f"V={Vv:.6g} V, I={Ii:.6g} A, R={Rr:.6g} Ω"
        if t.startswith('rc_cutoff'):
            parts = dict([p.strip().split('=') for p in t.split(' ',1)[1].split(',') if '=' in p]) if ' ' in t else {}
            R = _parse_value(parts.get('r',''))
            C = _parse_value(parts.get('c',''))
            fc = 1.0/(2*math.pi*R*C)
            return f"fc={fc:.6g} Hz"
        if t.startswith('divider'):
            parts = dict([p.strip().split('=') for p in t.split(' ',1)[1].split(',') if '=' in p]) if ' ' in t else {}
            Vin = _parse_value(parts.get('vin',''))
            R1 = _parse_value(parts.get('r1',''))
            R2 = _parse_value(parts.get('r2',''))
            Vout = Vin * (R2/(R1+R2))
            return f"Vout={Vout:.6g} V"
        # Fallback arithmetic
        expr = t.replace('^','**')
        for suf, mul in [('meg', 'e6'), ('g','e9'), ('k','e3'), ('m','e-3'), ('u','e-6'), ('µ','e-6'), ('n','e-9')]:
            expr = expr.replace(suf, mul)
        return str(eval(expr, {"__builtins__":{}}, {}))
    except Exception as e:
        return f"error: {str(e)}"

def _tool_memory_add(content: str) -> str:
    data = _read_persistent_memory()
    items = data.get('items') or []
    items.append({ 'text': content.strip(), 'ts': datetime.now(timezone.utc).isoformat() })
    data['items'] = items
    _write_persistent_memory(data)
    return "ok"

def _tool_memory_list(_: str) -> str:
    data = _read_persistent_memory()
    items = data.get('items') or []
    return json.dumps(items, ensure_ascii=False)

def _tool_memory_remove(match: str) -> str:
    data = _read_persistent_memory()
    items = data.get('items') or []
    m = (match or '').strip().lower()
    new_items = [it for it in items if m not in (it.get('text','').lower())]
    data['items'] = new_items
    _write_persistent_memory(data)
    return f"removed={len(items)-len(new_items)}"

def get_agent():
    global _AGENT_EXECUTOR
    if _AGENT_EXECUTOR is not None:
        return _AGENT_EXECUTOR
    if initialize_agent is None or Tool is None or ConversationBufferMemory is None:
        raise RuntimeError('LangChain agent components not available. Install requirements.')
    llm = get_llm()
    tools = [
        Tool(name='inventory', func=_tool_inventory_search, description='Search the inventory by component name and return matching items with quantities.'),
        Tool(name='search', func=_tool_web_search, description='Search the web for electronics specs or definitions when needed.'),
        Tool(name='electronics_calc', func=_tool_electronics_calc, description='Electronics calculations: ohms, rc_cutoff, divider, or arithmetic.'),
        Tool(name='add_to_memory', func=_tool_memory_add, description='Store a short memory string for later reference.'),
        Tool(name='list_memory', func=_tool_memory_list, description='List stored memory items.'),
        Tool(name='remove_from_memory', func=_tool_memory_remove, description='Remove memory items containing a substring.')
    ]
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    with _AGENT_LOCK:
        if _AGENT_EXECUTOR is None:
            _AGENT_EXECUTOR = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=False,
                memory=memory,
                handle_parsing_errors=True,
            )
    return _AGENT_EXECUTOR

 

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=20.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper functions for JSON response
def make_response(success, message, data=None):
    return jsonify({'success': success, 'message': message, 'data': data})

# CATEGORIES ENDPOINTS

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute('SELECT * FROM categories ORDER BY name')
        categories = [dict(row) for row in cursor.fetchall()]
        return make_response(True, 'Categories retrieved', categories)
    finally:
        if conn:
            conn.close()

@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return make_response(False, 'Name is required'), 400
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'INSERT INTO categories (name, description) VALUES (?, ?)',
            (name, description)
        )
        category_id = cursor.lastrowid
        conn.commit()
        return make_response(True, 'Category created successfully', {'id': category_id})
    except sqlite3.IntegrityError:
        return make_response(False, 'Category name already exists'), 400
    finally:
        if conn:
            conn.close()

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return make_response(False, 'Name is required'), 400
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'UPDATE categories SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (name, description, category_id)
        )
        conn.commit()
        return make_response(True, 'Category updated successfully')
    except sqlite3.IntegrityError:
        return make_response(False, 'Category name already exists'), 400
    finally:
        if conn:
            conn.close()

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    conn = None
    try:
        conn = get_db_connection()
        # Check if category has stocks
        cursor = conn.execute('SELECT COUNT(*) as count FROM stocks WHERE category_id = ?', (category_id,))
        count = cursor.fetchone()['count']
        
        if count > 0:
            return make_response(False, f'Cannot delete category with {count} stock item(s)'), 400
        
        cursor = conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        return make_response(True, 'Category deleted successfully')
    finally:
        if conn:
            conn.close()

# STOCKS ENDPOINTS

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    category_id = request.args.get('category_id', type=int)
    conn = None
    try:
        conn = get_db_connection()
        
        if category_id:
            cursor = conn.execute(
                'SELECT s.*, c.name as category_name FROM stocks s '
                'LEFT JOIN categories c ON s.category_id = c.id '
                'WHERE s.category_id = ? ORDER BY s.name',
                (category_id,)
            )
        else:
            cursor = conn.execute(
                'SELECT s.*, c.name as category_name FROM stocks s '
                'LEFT JOIN categories c ON s.category_id = c.id '
                'ORDER BY s.name'
            )
        
        stocks = [dict(row) for row in cursor.fetchall()]
        return make_response(True, 'Stocks retrieved', stocks)
    finally:
        if conn:
            conn.close()

@app.route('/api/stocks/<int:stock_id>', methods=['GET'])
def get_stock(stock_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'SELECT s.*, c.name as category_name FROM stocks s '
            'LEFT JOIN categories c ON s.category_id = c.id '
            'WHERE s.id = ?',
            (stock_id,)
        )
        stock = cursor.fetchone()
        
        if stock:
            return make_response(True, 'Stock retrieved', dict(stock))
        return make_response(False, 'Stock not found'), 404
    finally:
        if conn:
            conn.close()

@app.route('/api/stocks', methods=['POST'])
def create_stock():
    data = request.json
    name = data.get('name')
    category_id = data.get('category_id')
    quantity = data.get('quantity', 0)
    unit = data.get('unit', 'pcs')
    location = data.get('location', '')
    description = data.get('description', '')
    
    if not name or not category_id:
        return make_response(False, 'Name and category are required'), 400
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'INSERT INTO stocks (name, category_id, quantity, unit, location, description) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (name, category_id, quantity, unit, location, description)
        )
        stock_id = cursor.lastrowid
        conn.commit()
        return make_response(True, 'Stock created successfully', {'id': stock_id})
    except sqlite3.IntegrityError:
        return make_response(False, 'Category not found'), 400
    finally:
        if conn:
            conn.close()

@app.route('/api/stocks/<int:stock_id>', methods=['PUT'])
def update_stock(stock_id):
    data = request.json
    name = data.get('name')
    category_id = data.get('category_id')
    quantity = data.get('quantity')
    unit = data.get('unit')
    location = data.get('location')
    description = data.get('description')
    
    if not name:
        return make_response(False, 'Name is required'), 400
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'UPDATE stocks SET name = ?, category_id = ?, quantity = ?, unit = ?, '
            'location = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (name, category_id, quantity, unit, location, description, stock_id)
        )
        conn.commit()
        return make_response(True, 'Stock updated successfully')
    except sqlite3.IntegrityError:
        return make_response(False, 'Error updating stock'), 400
    finally:
        if conn:
            conn.close()

@app.route('/api/stocks/<int:stock_id>', methods=['DELETE'])
def delete_stock(stock_id):
    conn = None
    image_path = None
    try:
        conn = get_db_connection()
        
        # Get image path before deleting
        cursor = conn.execute('SELECT image_path FROM stocks WHERE id = ?', (stock_id,))
        stock = cursor.fetchone()
        if stock:
            image_path = stock['image_path']
        
        cursor = conn.execute('DELETE FROM stocks WHERE id = ?', (stock_id,))
        deleted = cursor.rowcount
        conn.commit()
        
        if deleted == 0:
            return make_response(False, 'Stock not found'), 404
        
        # Delete associated image if exists
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        
        return make_response(True, 'Stock deleted successfully')
    finally:
        if conn:
            conn.close()

@app.route('/api/stocks/<int:stock_id>/image', methods=['POST'])
def upload_stock_image(stock_id):
    if 'file' not in request.files:
        return make_response(False, 'No file provided'), 400
    
    file = request.files['file']
    if file.filename == '':
        return make_response(False, 'No file selected'), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add stock_id to make filename unique
        name, ext = os.path.splitext(filename)
        filename = f'stock_{stock_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}{ext}'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Update database with image path
        conn = None
        try:
            conn = get_db_connection()
            conn.execute('UPDATE stocks SET image_path = ? WHERE id = ?', (filepath, stock_id))
            conn.commit()
            return make_response(True, 'Image uploaded successfully', {'image_path': filepath})
        finally:
            if conn:
                conn.close()
    
    return make_response(False, 'Invalid file type'), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

 

# CONVERSATIONS ENDPOINTS

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'SELECT c.*, COUNT(m.id) as message_count FROM conversations c '
            'LEFT JOIN chat_messages m ON c.id = m.conversation_id '
            'GROUP BY c.id ORDER BY c.updated_at DESC'
        )
        conversations = [dict(row) for row in cursor.fetchall()]
        return make_response(True, 'Conversations retrieved', conversations)
    finally:
        if conn:
            conn.close()

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    data = request.json
    title = data.get('title', 'New Conversation')
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'INSERT INTO conversations (title) VALUES (?)',
            (title,)
        )
        conversation_id = cursor.lastrowid
        conn.commit()
        return make_response(True, 'Conversation created', {'id': conversation_id})
    finally:
        if conn:
            conn.close()

@app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    conn = None
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        conn.commit()
        return make_response(True, 'Conversation deleted')
    finally:
        if conn:
            conn.close()

@app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """Get all messages for a conversation"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.execute(
            'SELECT * FROM chat_messages WHERE conversation_id = ? ORDER BY created_at ASC',
            (conversation_id,)
        )
        messages = [dict(row) for row in cursor.fetchall()]
        return make_response(True, 'Messages retrieved', messages)
    finally:
        if conn:
            conn.close()

@app.route('/api/conversations/<int:conversation_id>/title', methods=['PUT'])
def update_conversation_title(conversation_id):
    """Update conversation title"""
    data = request.json
    title = data.get('title', '')
    
    if not title:
        return make_response(False, 'Title is required'), 400
    
    conn = None
    try:
        conn = get_db_connection()
        conn.execute(
            'UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (title, conversation_id)
        )
        conn.commit()
        return make_response(True, 'Title updated')
    finally:
        if conn:
            conn.close()

# AI Assistant endpoint with conversation support
@app.route('/api/ai/ask', methods=['POST'])
def ai_ask():
    try:
        data = request.json
        user_question = data.get('question', '')
        conversation_id = data.get('conversation_id', None)
        
        if not user_question:
            return make_response(False, 'Question is required'), 400
        
        # Ensure a conversation exists; create one if missing
        conn = get_db_connection()
        if not conversation_id:
            try:
                title_seed = (user_question or 'New Conversation').strip()[:60] or 'New Conversation'
                cur = conn.execute(
                    'INSERT INTO conversations (title, created_at, updated_at) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                    (title_seed,)
                )
                conversation_id = cur.lastrowid
                conn.commit()
            except Exception:
                pass

        # Get current inventory and categories
        cursor = conn.execute('SELECT s.name as name, s.quantity as quantity, s.unit as unit, c.name as category_name FROM stocks s LEFT JOIN categories c ON s.category_id = c.id LIMIT 10')
        stocks = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute('SELECT id, name FROM categories')
        categories = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Create context for AI
        inventory_summary = "\n".join([f"- {s['name']}: {s['quantity']} {s['unit']}" for s in stocks[:10]])
        categories_summary = "\n".join([f"- {c['name']} (id: {c['id']})" for c in categories])
        

        # Use LangChain Agent with tools and memory
        try:
            agent = get_agent()
            instructions = (
                "You are Stock Manager, an electronics inventory assistant. "
                "Use tools when needed. Never modify the database. "
                "When listing inventory, ALWAYS call the `inventory` tool and include a fenced JSON array in the answer like:\n"
                "```json\n[ { \"name\": \"1k resistor\", \"category\": \"Resistor\", \"quantity\": 10, \"unit\": \"pcs\" } ]\n```\n"
                "Keep any prose brief; the table data must be in that JSON."
            )
            context_text = (
                f"Current Inventory (sample):\n{inventory_summary}\n\n"
                f"Available Categories:\n{categories_summary}\n"
            )
            result = agent.invoke({"input": f"{instructions}\n\n{context_text}\nQuestion: {user_question}"})
            if isinstance(result, dict) and 'output' in result:
                answer = result['output']
            else:
                answer = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return make_response(False, f'LLM error: {str(e)}'), 500

        # Save messages to conversation if we have an id
        if conversation_id:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO chat_messages (conversation_id, role, message) VALUES (?, ?, ?)',
                (conversation_id, 'user', user_question)
            )
            conn.execute(
                'INSERT INTO chat_messages (conversation_id, role, message) VALUES (?, ?, ?)',
                (conversation_id, 'assistant', answer)
            )
            conn.commit()
            conn.close()

        table_rows = _extract_inventory_rows_from_text(answer)
        # If agent didn't provide JSON but the user intent is an inventory listing, fallback to direct inventory
        if not table_rows:
            intents = ['what i have', 'what have', 'ne var', 'envanter', 'list', 'liste', 'stoklar', 'what do i have']
            ql = (user_question or '').lower()
            if any(k in ql for k in intents):
                try:
                    raw = _tool_inventory_search('')
                    table_rows = json.loads(raw) if isinstance(raw, str) else (raw or [])
                except Exception:
                    table_rows = []
        payload = {
            'answer': answer,
            'model': get_llm_model_name(),
            'conversation_id': conversation_id
        }
        if table_rows:
            payload['inventory'] = table_rows
        return make_response(True, 'Answer generated', payload)

    except requests.exceptions.RequestException as e:
        return make_response(False, f'Network error: {str(e)}'), 500
    except Exception as e:
        return make_response(False, f'Error: {str(e)}'), 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def style():
    return send_from_directory('.', 'style.css', mimetype='text/css')

@app.route('/script.js')
def script():
    return send_from_directory('.', 'script.js', mimetype='application/javascript')

@app.route('/favicon.ico')
def favicon():
    # Simple SVG favicon - Electronic component icon
    svg_icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <rect x="10" y="30" width="80" height="40" rx="5" fill="#4CAF50" stroke="#2E7D32" stroke-width="2"/>
        <circle cx="25" cy="50" r="3" fill="#FFF"/>
        <circle cx="50" cy="50" r="3" fill="#FFF"/>
        <circle cx="75" cy="50" r="3" fill="#FFF"/>
        <text x="50" y="80" font-size="30" fill="#2E7D32" text-anchor="middle">📦</text>
    </svg>'''
    return svg_icon, 200, {'Content-Type': 'image/svg+xml'}

if __name__ == '__main__':
    # Check if database exists, if not create it
    if not os.path.exists(DATABASE):
        print(f"Database not found at {DATABASE}. Creating...")
        from database import init_database
        init_database(DATABASE)
    else:
        # Run lightweight migrations (adds missing timestamp columns)
        from database import init_database
        init_database(DATABASE)
    
    print("\n=== Stock Tracking Server ===")
    print("Server running on: http://0.0.0.0:5000")
    print("\nTo access from your phone:")
    print("1. Make sure your phone and laptop are on the same network")
    print("2. Find your laptop's IP address using: hostname -I")
    print("3. Access from phone: http://YOUR_IP:5000")
    print("\nStarting server...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)



