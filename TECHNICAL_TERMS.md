# Technical Terms - ezyZip Project

Comprehensive list of all technical terms, technologies, frameworks, libraries, and concepts used in the ezyZip Virtual Try-On Platform.

## Table of Contents
1. [Frontend Technologies](#frontend-technologies)
2. [Backend Technologies](#backend-technologies)
3. [AI/ML & Computer Vision](#aiml--computer-vision)
4. [APIs & Services](#apis--services)
5. [Data Formats & Protocols](#data-formats--protocols)
6. [Development Tools](#development-tools)
7. [Architecture Patterns](#architecture-patterns)
8. [Algorithms & Concepts](#algorithms--concepts)
9. [File Formats](#file-formats)
10. [System & Infrastructure](#system--infrastructure)

---

## Frontend Technologies

### Core Frameworks & Libraries
- **React 18** - JavaScript UI library for building user interfaces
- **TypeScript** - Typed superset of JavaScript
- **Vite** - Next-generation frontend build tool
- **Tailwind CSS** - Utility-first CSS framework
- **lucide-react** - Icon library for React

### React Concepts
- **React Hooks** - useState, useEffect, useContext
- **Context API** - CartContext for state management
- **Component-based Architecture** - Modular UI components
- **Functional Components** - React function components
- **Props** - Component properties
- **State Management** - React state hooks
- **Event Handlers** - User interaction handlers

### Frontend Tools
- **ESLint** - JavaScript/TypeScript linter
- **PostCSS** - CSS post-processor
- **Autoprefixer** - CSS vendor prefixing
- **npm** - Node Package Manager
- **Node.js 18+** - JavaScript runtime

### Frontend Patterns
- **Single Page Application (SPA)** - Client-side routing
- **RESTful API Client** - HTTP API consumption
- **FormData** - File upload handling
- **URLSearchParams** - Query string manipulation
- **Blob API** - Binary large object handling
- **Fetch API** - HTTP requests

---

## Backend Technologies

### Core Framework
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Python 3.10+** - Programming language
- **Pydantic** - Data validation using Python type annotations
- **Starlette** - ASGI framework (FastAPI dependency)

### Backend Libraries
- **python-multipart** - File upload support
- **python-dotenv** - Environment variable management
- **uuid** - Unique identifier generation

### Backend Patterns
- **REST API** - Representational State Transfer
- **CORS (Cross-Origin Resource Sharing)** - Cross-origin requests
- **Middleware** - Request/response processing
- **Static File Serving** - Asset delivery
- **File Upload** - Multipart form data handling
- **Streaming Response** - Image streaming
- **Query Parameters** - URL query string parsing
- **Path Parameters** - URL path variables
- **Request Body** - JSON payload handling

### Server Concepts
- **ASGI (Asynchronous Server Gateway Interface)** - Async Python web server interface
- **Hot Reload** - Development server auto-reload
- **Port Binding** - Network port configuration (8000)
- **Session Management** - In-memory game sessions

---

## AI/ML & Computer Vision

### Deep Learning Frameworks
- **PyTorch** - Deep learning framework
- **torchvision** - Computer vision utilities
- **torch.nn** - Neural network modules
- **torch.nn.functional** - Neural network functions
- **CUDA** - GPU acceleration
- **torch.no_grad()** - Inference mode (no gradient computation)

### Transformers & Models
- **Transformers** (Hugging Face) - Pre-trained model library
- **CLIP Model** - Contrastive Language-Image Pre-training
- **Fashion-CLIP** - Domain-specific CLIP model (patrickjohncyh/fashion-clip)
- **AutoProcessor** - Automatic tokenizer/processor loading

### Computer Vision Concepts
- **DM-VTON** - Distilled Mobile Real-time Virtual Try-On, the model this app uses
- **Parser-Free Try-On** - Try-on from the photo, garment and garment mask alone, with no pose estimation or human parsing at inference
- **Knowledge Distillation** - Training a small student model to imitate a larger parser-based teacher
- **Garment Mask** - Binary mask of the garment; the dataset's cloth-mask, or estimated from a plain background
- **Image Segmentation** - Pixel-level classification
- **Image Warping** - Geometric transformation
- **Appearance Flow** - Per-pixel offsets that warp the garment onto the body
- **Grid Sampling** - Spatial transformation sampling
- **Gaussian Blur** - Image smoothing filter
- **Bilinear Interpolation** - Image upscaling
- **Nearest Neighbor Interpolation** - Image resizing
- **Upsampling** - Resolution enhancement

### DM-VTON Components
- **MobileAFWM** - Mobile Appearance Flow Warping Module, warps the garment onto the person
- **MobileNetV2 FPN** - Lightweight feature pyramid used as the warping feature extractor
- **Correlation (Cost Volume)** - 7x7 feature matching between person and garment; CUDA kernel via cupy, or pure PyTorch on CPU
- **MobileNetV2 U-Net** - Generator that renders the person and a composition mask
- **Composition Mask** - Blends the warped garment with the rendered person
- **Automatic Person Framing** - Crops a photo with a lot of background to the catalogue framing the model was trained on

### Neural Network Concepts
- **Generator Networks** - Image generation models
- **Discriminator Networks** - Adversarial training (not used here)
- **Convolutional Neural Networks (CNN)** - Image processing networks
- **Checkpoints** - Saved model weights
- **Pre-trained Models** - Pre-trained network weights
- **Model Inference** - Prediction/generation phase
- **Batch Processing** - Multi-image processing
- **Device Placement** - CPU/GPU allocation

### Image Processing
- **PIL/Pillow** - Python Imaging Library
- **OpenCV** - Computer vision library
- **Image Preprocessing** - Input normalization
- **Image Postprocessing** - Output refinement
- **RGB Conversion** - Color space conversion
- **Image Resizing** - Dimension adjustment
- **Image Masking** - Region selection
- **Image Compositing** - Layer blending

### Machine Learning Concepts
- **Embeddings** - Vector representations
- **Feature Extraction** - Dimensionality reduction
- **Normalization** - Vector/feature normalization
- **L2 Normalization** - Euclidean normalization
- **Cosine Similarity** - Vector similarity metric
- **Semantic Search** - Meaning-based search
- **Vector Database** - Embedding storage

---

## APIs & Services

### Vector Database
- **Pinecone** - Vector database service
- **Pinecone Index** - Vector storage index
- **Vector Embeddings** - High-dimensional vectors
- **Cosine Metric** - Similarity measurement
- **Top-K Query** - Nearest neighbor search
- **Vector Upsert** - Insert/update vectors
- **Index Statistics** - Database metrics

### API Endpoints
- **REST Endpoints** - HTTP API routes
- **POST /start_game** - Game session initialization
- **GET /clothes_list** - Paginated garment listing
- **GET /search_clothes** - Semantic/filename search
- **POST /viton_preview_upload** - Virtual try-on generation
- **POST /pick** - Game pick submission
- **POST /rank** - Game ranking submission
- **GET /leaderboard** - Scoreboard retrieval
- **GET /recommend** - Recommendation endpoint
- **GET /api/ping** - Health check endpoint
- **GET /debug/*** - Debug utility endpoints

### API Concepts
- **HTTP Methods** - GET, POST
- **Status Codes** - 200, 404, 500
- **Request Headers** - Content-Type, CORS headers
- **Response Headers** - Access-Control-Allow-Origin
- **Query Strings** - URL parameters
- **Request Body** - JSON payloads
- **Multipart Form Data** - File upload format
- **Streaming Response** - Chunked data transfer

---

## Data Formats & Protocols

### Data Serialization
- **JSON** - JavaScript Object Notation
- **Base64** - Binary-to-text encoding
- **FormData** - Multipart form encoding
- **URL Encoding** - Percent encoding

### Image Formats
- **JPEG/JPG** - Lossy image compression
- **PNG** - Lossless image compression
- **RGB** - Red-Green-Blue color model

### Data Structures
- **Dictionaries** - Python key-value pairs
- **Lists/Arrays** - Ordered collections
- **Sets** - Unordered unique collections
- **Tuples** - Immutable sequences
- **Tensors** - Multi-dimensional arrays (PyTorch)
- **Numpy Arrays** - Numerical arrays

---

## Development Tools

### Version Control
- **Git** - Version control system
- **.gitignore** - Ignore file patterns

### Package Management
- **pip** - Python package installer
- **npm** - Node package manager
- **package.json** - Node.js dependencies
- **requirements.txt** - Python dependencies
- **package-lock.json** - Dependency lock file

### Virtual Environments
- **venv** - Python virtual environment
- **Virtual Environment Activation** - Shell environment setup

### Build Tools
- **Vite** - Frontend build tool
- **TypeScript Compiler** - TS to JS compilation
- **ESLint** - Code linting
- **PostCSS** - CSS processing

### Development Scripts
- **npm run dev** - Development server
- **npm run build** - Production build
- **uvicorn main:app --reload** - Backend dev server
- **quick_setup.bat** - Windows setup script

### Debugging
- **Console Logging** - Debug output
- **Print Statements** - Python debugging
- **Error Handling** - Try-catch blocks
- **Exception Handling** - Error management
- **Traceback** - Stack trace debugging

---

## Architecture Patterns

### Application Architecture
- **Client-Server Architecture** - Frontend-backend separation
- **API-First Design** - Backend API as contract
- **Microservices Pattern** - Modular service design
- **RESTful Architecture** - Resource-based API design

### State Management
- **In-Memory State** - Session storage
- **Context API** - React state sharing
- **Session Management** - Game session tracking
- **State Persistence** - Data retention (currently in-memory)

### Data Flow
- **Unidirectional Data Flow** - React data flow
- **API Calls** - HTTP requests
- **Async/Await** - Asynchronous programming
- **Promises** - Async operation handling
- **Callbacks** - Event handling

### Design Patterns
- **Component Pattern** - UI component reuse
- **Provider Pattern** - Context providers
- **Singleton Pattern** - Game state storage
- **Factory Pattern** - Object creation
- **Observer Pattern** - Event listening

---

## Algorithms & Concepts

### Game Logic
- **Round-Based Gameplay** - Multi-round sessions
- **Scoring Algorithm** - Point calculation
- **Leaderboard** - Ranking system
- **Pick System** - Player selection mechanism
- **Ranking System** - Ordering mechanism
- **Timer System** - Time-based constraints

### Search Algorithms
- **Semantic Search** - Meaning-based search
- **Vector Similarity Search** - Embedding comparison
- **Fallback Search** - Filename-based search
- **Pagination** - Page-based retrieval
- **Filtering** - Data filtering

### Image Processing Algorithms
- **Image Warping** - Geometric transformation
- **Grid Sampling** - Spatial sampling
- **Bilinear Interpolation** - Smooth upscaling
- **Gaussian Blur** - Noise reduction
- **Image Segmentation** - Region identification
- **Mask Generation** - Region masking
- **Image Compositing** - Layer blending

### Data Processing
- **Batch Processing** - Multi-item processing
- **Data Preprocessing** - Input preparation
- **Data Postprocessing** - Output refinement
- **Data Validation** - Input verification
- **Error Handling** - Exception management

---

## File Formats

### Code Files
- **.py** - Python source files
- **.tsx** - TypeScript React components
- **.ts** - TypeScript files
- **.js** - JavaScript files
- **.json** - JSON configuration
- **.css** - Cascading Style Sheets
- **.html** - HyperText Markup Language
- **.md** - Markdown documentation

### Configuration Files
- **package.json** - Node.js configuration
- **tsconfig.json** - TypeScript configuration
- **vite.config.ts** - Vite configuration
- **tailwind.config.js** - Tailwind CSS configuration
- **postcss.config.js** - PostCSS configuration
- **eslint.config.js** - ESLint configuration
- **requirements.txt** - Python dependencies
- **.env** - Environment variables
- **.gitignore** - Git ignore patterns

### Model Files
- **.pth** - PyTorch model checkpoint
- **.pkl** - Pickle serialized objects

### Data Files
- **.txt** - Text files (test pairs, configuration)
- **.jpg/.jpeg** - JPEG images
- **.png** - PNG images
- **.json** - JSON data files

---

## System & Infrastructure

### Operating System
- **Windows 10/11** - OS platform
- **PowerShell** - Shell environment
- **Batch Scripts** - .bat files

### Hardware Requirements
- **GPU** - Graphics Processing Unit (CUDA)
- **CPU** - Central Processing Unit
- **CUDA** - NVIDIA GPU computing platform
- **GPU Memory** - VRAM for model inference

### Network
- **HTTP** - Hypertext Transfer Protocol
- **HTTPS** - Secure HTTP
- **Localhost** - Local development server
- **Port 8000** - Backend server port
- **Port 5173** - Vite dev server port
- **CORS** - Cross-Origin Resource Sharing

### File System
- **Directory Structure** - Folder organization
- **Path Resolution** - File path handling
- **Relative Paths** - Path relative to current directory
- **Absolute Paths** - Full file system paths
- **File I/O** - File input/output operations

### Environment
- **Environment Variables** - Configuration via env vars
- **API Keys** - Service authentication keys
- **Configuration Management** - Settings management
- **Secret Management** - Credential storage

### Dataset Structure
- **Training Split** - Train dataset partition
- **Test Split** - Test dataset partition
- **Image Directories** - Folder organization
- **Mask Directories** - Segmentation masks
- **Pose and Parse Directories** - Present in VITON-HD, not needed by DM-VTON
- **Pair Files** - Test pair configurations

### What DM-VTON Needs From The Dataset
- **Person Images** - image/
- **Cloth Images** - cloth/
- **Cloth Masks** - cloth-mask/ (estimated when absent, e.g. for uploaded garments)

---

## Additional Technical Concepts

### Software Engineering
- **Code Organization** - Project structure
- **Modular Design** - Component separation
- **Separation of Concerns** - Architecture principle
- **DRY (Don't Repeat Yourself)** - Code reuse
- **SOLID Principles** - Object-oriented design
- **API Design** - Interface design
- **Error Handling** - Exception management
- **Logging** - Debug output
- **Testing** - Quality assurance (prepared for)

### Performance Optimization
- **GPU Acceleration** - Hardware acceleration
- **Batch Processing** - Efficient processing
- **Lazy Loading** - On-demand loading
- **Caching** - Data caching (prepared for)
- **Image Optimization** - Asset optimization
- **Code Splitting** - Bundle optimization

### Security
- **CORS Configuration** - Cross-origin security
- **API Key Management** - Credential security
- **Input Validation** - Data validation
- **File Upload Security** - Upload safety
- **Environment Variables** - Secret management

### Deployment (Prepared For)
- **Docker** - Containerization (mentioned in README)
- **CI/CD** - Continuous Integration/Deployment (mentioned)
- **Production Build** - Optimized build
- **Static File Serving** - Asset delivery
- **Reverse Proxy** - Server configuration

---

## Domain-Specific Terms

### Fashion & E-commerce
- **Virtual Try-On** - Digital garment fitting
- **Garment** - Clothing item
- **Catalog** - Product inventory
- **Shopping Cart** - Purchase selection
- **Product Recommendations** - Item suggestions
- **Style Game** - Fashion selection game
- **Styling** - Outfit coordination

### Gaming
- **Multiplayer Game** - Multi-player session
- **Round-Based** - Turn-based gameplay
- **Session ID** - Game session identifier
- **Player** - Game participant
- **Score** - Point accumulation
- **Leaderboard** - Ranking display
- **Timer** - Time constraint
- **Pick** - Selection action
- **Ranking** - Ordering action

### Computer Vision (VITON)
- **Agnostic Representation** - Clothing-agnostic person image
- **Warped Cloth** - Deformed garment
- **Parse Map** - Segmentation map
- **Pose Keypoints** - Body joint locations
- **Misalignment** - Geometric mismatch
- **Normalization** - Feature normalization
- **Generator** - Image synthesis network
- **High-Resolution** - 1024x768 output
- **Try-On Synthesis** - Virtual fitting generation

---

## Summary Statistics

- **Total Technologies**: 150+ technical terms
- **Frontend Technologies**: 20+
- **Backend Technologies**: 15+
- **AI/ML Technologies**: 40+
- **APIs & Services**: 10+
- **Development Tools**: 15+
- **Architecture Patterns**: 10+
- **Algorithms & Concepts**: 20+
- **File Formats**: 15+
- **System & Infrastructure**: 15+

---

*Last Updated: Based on current codebase analysis*
*This document serves as a comprehensive reference for all technical terms used in the ezyZip project.*

