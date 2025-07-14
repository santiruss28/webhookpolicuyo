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

from flask import Response
@app.route('/cotizar', methods=['POST'])
def cotizar():
    try:
        if not request.is_json:
            return Response("❌ La solicitud debe enviarse como JSON", content_type="text/plain"), 400

        data = request.get_json()
        texto = ""
        all_resultados = []

        if 'consulta' in data:
            consultas = [{'consulta': data['consulta'], 'segmento': data.get('segmento', '')}]
        elif 'consultas' in data:
            consultas = data['consultas']
        else:
            return Response("❌ Faltan los campos 'consulta' o 'consultas'", content_type="text/plain"), 400

        for item in consultas:
            consulta = item.get('consulta', '').strip()
            segmento = item.get('segmento', '').strip()
            if not consulta:
                continue

            resultados = search_products(consulta, segmento if segmento else None)
            all_resultados.extend(resultados)

            texto += f"🔎 *Consulta:* {consulta}\n"
            if resultados:
                for r in resultados[:5]:  # Mostramos hasta 5 resultados por ítem
                    texto += (
                        f"• {r['descripcion']}\n"
                        f"  - 💵 Contado: ${r['precio_contado']}\n"
                        f"  - 💳 Tarjeta: ${r['precio_tarjeta']}\n"
                        f"  - 🏷️ Segmento: {r['segmento']}\n"
                    )
                    if 'score' in r:
                        texto += f"  - 🎯 Similitud: {r['score']}\n"
                    texto += "\n"
            else:
                texto += "⚠️ No se encontraron coincidencias.\n\n"

        # Calcular total
        def to_float(valor):
            try:
                return float(str(valor).replace('.', '').replace(',', '.'))
            except:
                return 0.0

        total = sum(to_float(r['precio_contado']) for r in all_resultados)
        texto += f"🧮 *Total estimado (contado):* ${total:,.2f}\n"

        # Agregamos aviso si hay demasiadas coincidencias similares
        if len(all_resultados) > 3:
            texto += "\nℹ️ Si alguno de estos productos no coincide con lo que necesitás, podés indicarnos el tipo, marca o alguna característica para afinar la búsqueda."

        return Response(texto, content_type="text/plain"), 200

    except Exception as e:
        return Response(f"❌ Error interno: {str(e)}", content_type="text/plain"), 500


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
