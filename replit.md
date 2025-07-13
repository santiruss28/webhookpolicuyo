# Product Search API

## Overview

This is a Flask-based web API for searching products from a CSV file using fuzzy string matching. The application loads product data from a CSV file and provides search functionality through HTTP endpoints using RapidFuzz for intelligent text matching. The system now includes segment-based filtering and improved matching algorithms for better search results.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a simple monolithic architecture built on Flask, a lightweight Python web framework. The system is designed as a stateless API service that loads product data into memory for fast search operations.

### Core Components:
- **Flask Web Server**: Handles HTTP requests and responses
- **In-Memory Data Store**: CSV data loaded into pandas DataFrame for fast querying
- **Fuzzy Search Engine**: RapidFuzz library for intelligent text matching
- **Logging System**: Built-in Python logging for debugging and monitoring

## Key Components

### 1. Data Layer (`app.py`)
- **Product Data Management**: Uses pandas DataFrame to store product information in memory
- **CSV File Integration**: Loads product data from `listado.csv` file
- **Data Validation**: Ensures required columns exist (`Descripcion`, `Precio Contado`, `Precio Tarjeta`, `Segmento`)
- **Segment Classification**: Products are organized into categories (Computadoras, Periféricos, Audio, etc.)

### 2. Search Engine (`app.py`)
- **Enhanced Fuzzy Matching**: Implements RapidFuzz's `partial_ratio` algorithm for text similarity on both description and segment fields
- **Intelligent Scoring**: Uses maximum score between description and segment matching with boost for segment matches
- **Segment Filtering**: Optional parameter to filter search results by product segment
- **Configurable Threshold**: Uses minimum score parameter (default 90) to filter results
- **Score-based Results**: Returns matches with similarity scores for ranking

### 3. Web API Layer (`app.py`)
- **Flask Application**: Provides RESTful API endpoints
- **Request Handling**: Processes HTTP requests and returns JSON responses
- **Enhanced Endpoints**: 
  - `/` - Health check endpoint
  - `/cotizar` - Product search with single or multiple query support and optional segment filtering
  - `/segmentos` - List all available product segments
- **Error Handling**: Comprehensive error handling and logging

### 4. Application Entry Point (`main.py`)
- **Server Configuration**: Runs Flask app on host 0.0.0.0, port 5000
- **Development Mode**: Enables debug mode for development

## Data Flow

1. **Application Startup**: 
   - Load CSV file into pandas DataFrame
   - Validate required columns exist
   - Initialize Flask application

2. **Search Request Processing**:
   - Support for single query (`{"consulta": "item"}`) or multiple queries (`{"consultas": [{"consulta": "item1", "segmento": "category"}, ...]}`)
   - Iterate through all products in DataFrame for each query
   - Calculate fuzzy match score for each product description and segment
   - Filter results based on minimum score threshold
   - For multiple queries: combine results and eliminate duplicates
   - Return matching products with scores

3. **Response Format**:
   - JSON array of matching products
   - Each result includes: description, cash price, card price, segment, and match score
   - Optional segment filtering information when applicable

## External Dependencies

### Core Libraries:
- **Flask**: Web framework for API endpoints
- **pandas**: Data manipulation and CSV file handling
- **rapidfuzz**: Fast fuzzy string matching algorithms

### System Dependencies:
- **Python 3.x**: Runtime environment
- **CSV File**: `listado.csv` containing product data

## Deployment Strategy

### Current Configuration:
- **Development Mode**: Flask debug mode enabled
- **Network Binding**: Configured to accept connections from any IP (0.0.0.0)
- **Port**: Default port 5000
- **Session Management**: Uses environment variable for session secret

### Production Considerations:
- Disable debug mode in production
- Use proper WSGI server (like Gunicorn)
- Implement proper error handling and logging
- Add input validation and sanitization
- Consider database migration for larger datasets
- Implement caching for frequently searched terms

### Environment Variables:
- `SESSION_SECRET`: Flask session secret key (falls back to default if not set)

## Technical Notes

### Data Storage Approach:
The application loads all product data into memory using pandas DataFrame. This approach provides:
- **Pros**: Fast search operations, simple implementation
- **Cons**: Memory usage scales with data size, data reloads require restart

### Search Algorithm:
Uses RapidFuzz's `partial_ratio` algorithm which:
- Handles partial matches within product descriptions
- Provides similarity scores for result ranking
- Performs case-insensitive matching

### Scalability Considerations:
- Current in-memory approach suitable for small to medium datasets
- For larger datasets, consider database integration
- Search performance may degrade with very large product catalogs