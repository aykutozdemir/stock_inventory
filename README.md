# Electronic Components Inventory

[![Python](https://img.shields.io/badge/python-3.11+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![LangChain](https://img.shields.io/badge/langchain-FF6F00?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain.com)

A modern electronic component inventory management system with a local AI-powered assistant. Features intelligent component search, automatic datasheet retrieval, specification extraction, and conversation-based interactions. Built with Flask backend and modern web frontend, running entirely on your machine with local LLM support.

## 🚀 Features

### Core Functionality
- **Component Management**: Add, edit, delete electronic components with categories
- **Stock Tracking**: Monitor quantity, location, and stock levels  
- **Image Upload**: Attach component images for easy identification
- **Search & Filter**: Advanced search and filtering capabilities
- **Table & Card Views**: Toggle between detailed table view and card view

### AI-Powered Features
- **Local LLM Assistant**: Ask questions about your inventory in natural language
- **Real-time Progress**: Step-by-step progress updates during AI processing
- **Datasheet Retrieval**: Automatic PDF datasheet download and analysis
- **Specification Extraction**: Extract key specs (voltage, current, power, package, etc.)
- **Component Research**: Search online for component specifications
- **Electronics Calculations**: Built-in calculator for circuit calculations
- **Conversation Management**: Save and manage conversation history
- **Multi-Component Datasheets**: Intelligent extraction of specs for specific components from multi-variant datasheets

### Technical Highlights
- **Local AI**: Runs entirely offline using llama.cpp (GGUF models)
- **Gemma 3 Support**: Optimized for Gemma 3 4B and 12B models
- **Dynamic Model Selection**: Automatically selects best model based on available VRAM
- **Modular Architecture**: Clean separation with blueprints, services, and repositories
- **RESTful API**: Well-structured API endpoints
- **Security**: Input validation, sanitization, and rate limiting
- **Progress Streaming**: Real-time Server-Sent Events for AI progress updates

## 🏗️ Architecture

```
electronic-component-inventory/
├── backend/                 # Flask backend application
│   ├── blueprints/         # API route handlers (ai, stocks, categories, conversations, datasheets)
│   ├── services/          # Business logic layer
│   │   ├── ai_service.py         # LLM integration and AI operations
│   │   ├── datasheet_service.py  # Datasheet management
│   │   ├── web_scraping_service.py # Component spec search
│   │   └── ...
│   ├── repositories/      # Data access layer
│   ├── models/           # Database models
│   ├── utils/            # Utility functions (security, validation, logging)
│   └── config.py         # Application configuration
├── frontend/              # Web frontend
│   ├── index.html        # Main HTML
│   └── static/
│       ├── css/style.css  # Styles
│       └── js/script.js   # Frontend logic
├── models/                # LLM model files (.gguf format)
├── tests/                 # Test suite
├── tray_app.py           # System tray application
├── run.sh                # Start script
├── install.sh            # Installation script
└── requirements.txt      # Python dependencies
```

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher
- Linux (tested on Ubuntu/Debian)
- GPU (optional but recommended for faster inference)
- 4GB+ RAM (8GB+ recommended)
- 2GB+ free disk space for models

### Quick Start

```bash
# Clone the repository
git clone https://github.com/aykutozdemir/stock_inventory.git
cd stock_inventory

# Make scripts executable
chmod +x install.sh run.sh stop.sh

# Install dependencies and setup
./install.sh

# Start the application
./run.sh

# Access at http://localhost:5000
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (auto-initializes on first run)
# Database will be created automatically

# Run the application
python backend/app.py
# or use the tray app
python tray_app.py
```

### Model Setup

The application automatically discovers and selects the best `.gguf` model from the `models/` directory based on your hardware.

**Download Models:**

Place `.gguf` model files in the `models/` directory. Recommended models:

- **Gemma 3 4B IT** (Q4_0 quantization) - ~2.5GB, good for 4GB VRAM
- **Gemma 3 12B IT** (Q4_0 quantization) - ~7GB, requires 8GB+ VRAM

You can download models from Hugging Face or other sources. The app supports any llama.cpp-compatible GGUF model.

**Model Selection:**

The system automatically:
1. Detects available VRAM
2. Selects appropriate model and quantization
3. Falls back gracefully if memory is insufficient
4. Uses CPU-only mode if GPU unavailable

Set a specific model via environment variable:
```bash
export LLM_MODEL=gemma-3-12b-it-q4_0
./run.sh
```

## 📖 Usage

### Web Interface

1. **Categories Tab**: Organize components into categories (Resistors, Capacitors, Diodes, ICs, etc.)
2. **Components Tab**: Add, edit, and manage component inventory
3. **AI Assistant Tab**: 
   - Ask questions about inventory: "How many resistors do I have?"
   - Request datasheets: "Find datasheet for 1N4148"
   - Get specifications: "What are the specs for LM358?"
   - Calculate values: "Calculate voltage divider with R1=10k, R2=5k, Vin=12V"

### AI Assistant Examples

```
"Show me all diodes"
"What is the specification of 1N4007?"
"Find datasheet for LM358 op amp"
"How many components do I have in total?"
"Calculate ohms law V=5, R=2k"
"What's the resistance for series 4k and 5k resistors?"
```

### API Usage

```bash
# Get all categories
curl http://localhost:5000/api/categories

# Add a new component
curl -X POST http://localhost:5000/api/stocks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "1N4148",
    "category_id": 1,
    "quantity": 100,
    "unit": "pcs",
    "description": "Fast switching diode"
  }'

# Ask AI assistant (regular endpoint)
curl -X POST http://localhost:5000/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many diodes do I have?", "conversation_id": null}'

# Ask AI assistant (streaming endpoint with progress)
curl -X POST http://localhost:5000/api/ai/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Find datasheet for 1N4007", "conversation_id": null}'
```

## 🔧 Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_MODEL=gemma-3-12b-it-q4_0          # Specific model name (optional)
MODEL_DIR=models                        # Model directory (default: models/)

# Flask Configuration
FLASK_ENV=production                    # or development
FLASK_DEBUG=false                       # or true
SECRET_KEY=your-secret-key-here         # Change in production!

# Database
DATABASE=inventory.db                   # SQLite database file

# Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800             # 50MB

# Logging
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR
LOG_FILE=app.log
```

### Hardware Configuration

The system auto-detects hardware and creates `hardware_config.json`. You can manually edit it:

```json
{
  "n_threads": 8,
  "n_ctx": 8192,
  "gpu_layers": -1,
  "detected_vram_mb": 4096,
  "detected_cpu_threads": 16
}
```

**Context Length:** Default is 8192 tokens (supports long datasheet summaries). Can be reduced to 4096 or 2048 for systems with limited memory.

## 📊 API Documentation

### Categories
- `GET /api/categories` - List all categories
- `POST /api/categories` - Create new category
- `PUT /api/categories/{id}` - Update category
- `DELETE /api/categories/{id}` - Delete category

### Stocks (Components)
- `GET /api/stocks` - List all stock items (with filters)
- `POST /api/stocks` - Create new stock item
- `PUT /api/stocks/{id}` - Update stock item
- `DELETE /api/stocks/{id}` - Delete stock item
- `GET /api/stocks/{id}` - Get stock details

### Conversations
- `GET /api/conversations` - List all conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/{id}/messages` - Get conversation messages
- `POST /api/conversations/{id}/messages` - Add message to conversation
- `DELETE /api/conversations/{id}` - Delete conversation

### Datasheets
- `GET /api/datasheets/{id}` - Download/view datasheet PDF
- `GET /api/datasheets/{id}/summary` - Get datasheet summary

### AI Endpoints
- `POST /api/ai/ask` - Ask AI assistant (standard request)
- `POST /api/ai/ask/stream` - Ask AI with real-time progress (Server-Sent Events)
- `POST /api/ai/calculate` - Electronics calculations
- `POST /api/ai/search` - Component search

## 🔒 Security Features

- **Input Validation**: Comprehensive validation for all user inputs
- **SQL Injection Protection**: Parameterized queries and input sanitization
- **XSS Protection**: HTML escaping and content sanitization
- **Rate Limiting**: API rate limiting to prevent abuse
- **File Upload Security**: File type validation and secure filename handling
- **CORS Configuration**: Configurable CORS origins

## 🧪 Testing

```bash
# Run basic tests
python tests/test_basic.py

# Test CUDA installation (if using GPU)
python tests/test_cuda_install.py

# Test model loading
python -m pytest tests/
```

## 🐛 Troubleshooting

### Model Loading Issues

**No models found:**
```bash
# Ensure models directory exists
mkdir -p models

# Download a model (example with huggingface-cli)
huggingface-cli download google/gemma-3-4b-it-gguf gemma-3-4b-it-q4_0.gguf --local-dir models/
```

**Out of memory:**
- Reduce `n_ctx` in `hardware_config.json` (e.g., 4096 or 2048)
- Use smaller model (4B instead of 12B)
- Reduce `gpu_layers` or use CPU-only mode

**Slow inference:**
- Enable GPU acceleration (check `gpu_layers` in `hardware_config.json`)
- Use higher quantization (Q8 instead of Q4) if VRAM allows
- Increase `n_threads` for CPU-only mode

### Database Issues

```bash
# Reinitialize database (WARNING: deletes all data)
rm inventory.db
python -c "from backend.models.database import init_db; init_db()"
```

### Port Already in Use

```bash
# Find and kill process using port 5000
sudo lsof -ti:5000 | xargs kill -9
# Or change port in backend/app.py
```

## 📝 Project Details

**Language**: Python 3.11+
**Framework**: Flask
**Database**: SQLite
**AI**: LangChain + llama.cpp (LlamaCpp)
**Models**: Gemma 3 (4B/12B) or any GGUF-compatible model
**Frontend**: Vanilla JavaScript, HTML5, CSS3

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Flask framework for the web application
- SQLite for lightweight database storage
- LangChain for AI integration
- llama.cpp for local LLM inference
- Google Gemma models for AI capabilities
- Modern web technologies for the frontend

## 📞 Support

For issues, questions, or contributions, please open an issue on [GitHub](https://github.com/aykutozdemir/stock_inventory).

---

**Version**: 2.0.0  
**Repository**: https://github.com/aykutozdemir/stock_inventory  
**Last Updated**: 2025
