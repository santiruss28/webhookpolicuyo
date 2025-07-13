import os
import logging
import pandas as pd
from flask import Flask, request, jsonify
from rapidfuzz import fuzz

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Global variable to store product data
products_df = None

def load_products():
    """Load products from CSV file"""
    global products_df
    try:
        products_df = pd.read_csv('listado.csv', sep=';')
        logging.info(f"Loaded {len(products_df)} products from CSV")
        # Ensure required columns exist
        required_columns = ['Descripcion', 'Precio Contado', 'Precio Tarjeta', 'SEGMENTO']
        if not all(col in products_df.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {required_columns}")
        return True
    except Exception as e:
        logging.error(f"Error loading products: {str(e)}")
        return False

def search_products(query, segmento=None, min_score=90):
    """Search products using fuzzy matching with optional segment filtering"""
    if products_df is None:
        raise ValueError("Products not loaded")
    
    results = []
    
    # Filter by segment if provided
    df_filtered = products_df
    if segmento:
        df_filtered = products_df[products_df['SEGMENTO'].str.lower() == segmento.lower()]
        if df_filtered.empty:
            logging.info(f"No products found in segment: {segmento}")
            return results
    
    for index, row in df_filtered.iterrows():
        # Calculate similarity scores for different fields
        desc_score = fuzz.partial_ratio(query.lower(), str(row['Descripcion']).lower())
        segment_score = fuzz.partial_ratio(query.lower(), str(row['SEGMENTO']).lower())
        
        # Use the highest score between description and segment
        # Give slight boost if segment matches to improve relevance
        final_score = max(desc_score, segment_score)
        if segment_score >= 80:  # Boost for segment matches
            final_score = min(100, final_score + 10)
        
        if final_score >= min_score:
            result = {
                'descripcion': str(row['Descripcion']),
                'precio_contado': row['Precio Contado'],
                'precio_tarjeta': row['Precio Tarjeta'],
                'segmento': str(row['SEGMENTO']),
                'score': final_score
            }
            results.append(result)
    
    # Sort results by score in descending order
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"message": "Webhook activo"}), 200

@app.route('/segmentos', methods=['GET'])
def get_segmentos():
    """Get all available segments"""
    try:
        if products_df is None:
            return jsonify({"error": "Products not loaded"}), 500
            
        # Get unique segments
        segmentos = sorted(products_df['SEGMENTO'].unique().tolist())
        
        # Count products per segment
        segment_counts = products_df['SEGMENTO'].value_counts().to_dict()
        
        segmentos_info = []
        for seg in segmentos:
            segmentos_info.append({
                "segmento": seg,
                "cantidad_productos": segment_counts.get(seg, 0)
            })
        
        return jsonify({
            "segmentos": segmentos_info,
            "total_segmentos": len(segmentos)
        }), 200
        
    except Exception as e:
        logging.error(f"Error in /segmentos: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/cotizar', methods=['POST'])
def cotizar():
    """Main endpoint for product quotation"""
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json"
            }), 400
        
        # Get JSON data
        data = request.get_json()
        
        # Check if it's a single query or multiple queries
        if 'consulta' in data:
            # Single query format (backward compatibility)
            consulta = data['consulta']
            segmento = data.get('segmento', None)
            
            # Validate consulta is not empty
            if not consulta or not isinstance(consulta, str) or not consulta.strip():
                return jsonify({
                    "error": "Field 'consulta' must be a non-empty string"
                }), 400
            
            # Validate segmento if provided
            if segmento is not None and (not isinstance(segmento, str) or not segmento.strip()):
                return jsonify({
                    "error": "Field 'segmento' must be a non-empty string when provided"
                }), 400
            
            logging.info(f"Processing single query: {consulta}" + (f" in segment: {segmento}" if segmento else ""))
            
            # Search for products
            results = search_products(consulta.strip(), segmento.strip() if segmento else None)
            
            response_data = {
                "consulta": consulta,
                "resultados": results,
                "total_encontrados": len(results)
            }
            
            if segmento:
                response_data["segmento_filtrado"] = segmento
                
        elif 'consultas' in data:
            # Multiple queries format
            consultas = data['consultas']
            
            if not isinstance(consultas, list) or not consultas:
                return jsonify({
                    "error": "Field 'consultas' must be a non-empty array"
                }), 400
            
            all_results = []
            consultas_procesadas = []
            
            for i, item in enumerate(consultas):
                if not isinstance(item, dict):
                    return jsonify({
                        "error": f"Item {i+1} in 'consultas' must be an object with 'consulta' field"
                    }), 400
                
                if 'consulta' not in item:
                    return jsonify({
                        "error": f"Item {i+1} in 'consultas' is missing required field 'consulta'"
                    }), 400
                
                consulta = item['consulta']
                segmento = item.get('segmento', None)
                
                if not consulta or not isinstance(consulta, str) or not consulta.strip():
                    return jsonify({
                        "error": f"Field 'consulta' in item {i+1} must be a non-empty string"
                    }), 400
                
                if segmento is not None and (not isinstance(segmento, str) or not segmento.strip()):
                    return jsonify({
                        "error": f"Field 'segmento' in item {i+1} must be a non-empty string when provided"
                    }), 400
                
                logging.info(f"Processing query {i+1}: {consulta}" + (f" in segment: {segmento}" if segmento else ""))
                
                # Search for this specific query
                item_results = search_products(consulta.strip(), segmento.strip() if segmento else None)
                
                consulta_info = {
                    "consulta": consulta,
                    "resultados": item_results,
                    "total_encontrados": len(item_results)
                }
                
                if segmento:
                    consulta_info["segmento_filtrado"] = segmento
                
                consultas_procesadas.append(consulta_info)
                all_results.extend(item_results)
            
            # Remove duplicates based on product description
            seen_descriptions = set()
            unique_results = []
            for result in all_results:
                if result['descripcion'] not in seen_descriptions:
                    seen_descriptions.add(result['descripcion'])
                    unique_results.append(result)
            
            # Sort by score
            unique_results.sort(key=lambda x: x['score'], reverse=True)
            
            response_data = {
                "consultas_procesadas": consultas_procesadas,
                "resultados_combinados": unique_results,
                "total_consultas": len(consultas),
                "total_encontrados_combinados": len(unique_results)
            }
            
        else:
            return jsonify({
                "error": "Missing required field. Use 'consulta' for single search or 'consultas' for multiple searches"
            }), 400
        
        # Log results based on query type
        if 'consulta' in data:
            logging.info(f"Found {len(response_data['resultados'])} matching products for single query")
        else:
            logging.info(f"Processed {len(response_data['consultas_procesadas'])} queries, found {len(response_data['resultados_combinados'])} unique products")
            
        return jsonify(response_data), 200
        
    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return jsonify({
            "error": f"Data error: {str(ve)}"
        }), 500
        
    except Exception as e:
        logging.error(f"Unexpected error in /cotizar: {str(e)}")
        return jsonify({
            "error": "Internal server error occurred while processing request"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

# Load products on startup
if not load_products():
    logging.error("Failed to load products on startup")

if __name__ == '__main__':
    # Ensure products are loaded before starting server
    if products_df is None:
        logging.warning("Starting server without product data - check listado.csv file")
    
    # Start Flask server
    app.run(host="0.0.0.0", port=3000, debug=True)
