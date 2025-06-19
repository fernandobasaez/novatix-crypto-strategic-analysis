from flask import Flask, request, jsonify
import re
import json

app = Flask(__name__)

@app.route('/extract-crypto-actions', methods=['POST'])
def extract_crypto_actions():
    try:
        # Obtener datos raw y limpiar caracteres problemáticos
        raw_data = request.get_data(as_text=True)

        # Limpiar el JSON de caracteres de control problemáticos
        # Reemplazar \n, \r, \t con espacios
        cleaned_data = raw_data.replace('\\n', ' ').replace('\\r', ' ').replace('\\t', ' ')
        # También limpiar saltos de línea reales
        cleaned_data = cleaned_data.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        try:
            data = json.loads(cleaned_data)
        except json.JSONDecodeError as e:
            # Si aún falla, intentar con una limpieza más agresiva
            # Extraer solo lo que necesitamos del texto crudo
            ai_response = extract_ai_response_from_raw(raw_data)
            if ai_response:
                data = {'ai_response': ai_response}
            else:
                return jsonify({
                    'success': False,
                    'error': f'JSON parse error: {str(e)}',
                    'raw_data_preview': raw_data[:200],
                    'recommendation': 'HOLD',
                    'btc_action': 'HOLD',
                    'btc_percentage': '0%',
                    'eth_action': 'HOLD',
                    'eth_percentage': '0%',
                    'sol_action': 'HOLD',
                    'sol_percentage': '0%',
                    'market_cycle': 'NEUTRAL'
                }), 400

        # Extraer ai_response
        ai_response = data.get('ai_response', '')

        # Procesar con las funciones extract
        recommendation = extract_recommendation(ai_response)

        btc_action = extract_action(ai_response, 'BTC')
        btc_percentage = extract_percentage(ai_response, 'BTC')

        eth_action = extract_action(ai_response, 'ETH')
        eth_percentage = extract_percentage(ai_response, 'ETH')

        sol_action = extract_action(ai_response, 'SOL')
        sol_percentage = extract_percentage(ai_response, 'SOL')

        # UN SOLO RETURN con todo incluido
        return jsonify({
            'success': True,
            'recommendation': recommendation,
            'btc_action': btc_action,
            'btc_percentage': btc_percentage,
            'eth_action': eth_action,
            'eth_percentage': eth_percentage,
            'sol_action': sol_action,
            'sol_percentage': sol_percentage,
            'market_cycle': extract_market_cycle(ai_response)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'General error: {str(e)}',
            'recommendation': 'HOLD',
            'btc_action': 'HOLD',
            'btc_percentage': '0%',
            'eth_action': 'HOLD',
            'eth_percentage': '0%',
            'sol_action': 'HOLD',
            'sol_percentage': '0%',
            'market_cycle': 'NEUTRAL'
        }), 500

def extract_ai_response_from_raw(raw_data):
    """Extraer ai_response del JSON crudo cuando el parsing normal falla"""
    try:
        # Buscar el patrón "ai_response": "..." en el texto
        import re
        pattern = r'"ai_response":\s*"([^"]*(?:\\.[^"]*)*)"'
        match = re.search(pattern, raw_data)
        if match:
            # Limpiar el texto extraído
            ai_text = match.group(1)
            # Decodificar escapes básicos
            ai_text = ai_text.replace('\\"', '"').replace('\\\\', '\\')
            return ai_text
    except:
        pass
    return None

def extract_recommendation(text):
    pattern = r'RECOMMENDATION:\s*(ACCUMULATE|REBALANCE|REDUCE|HOLD)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).upper() if match else 'HOLD'

def extract_action(text, crypto):
    pattern = f'{crypto}_ACTION:\s*(COMPRAR|VENDER|HOLD)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).upper() if match else 'HOLD'

def extract_percentage(text, crypto):
    pattern = f'{crypto}_PERCENTAGE:\s*([+-]?\d+\.?\d*%?)'
    match = re.search(pattern, text)
    if match:
        percentage = match.group(1)
        if not percentage.endswith('%'):
            percentage += '%'
        return percentage
    return '0%'

def extract_market_cycle(text):
    text_upper = text.upper()
    if any(word in text_upper for word in ["ALCISTA", "BULL", "SUBIDA", "POSITIVO"]):
        return "BULL_MARKET"
    elif any(word in text_upper for word in ["BAJISTA", "BEAR", "BAJADA", "NEGATIVO"]):
        return "BEAR_MARKET"
    elif any(word in text_upper for word in ["CORRECCIÓN", "CORRECTION", "AJUSTE"]):
        return "CORRECTION"
    return "NEUTRAL"

# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Crypto Actions Webhook is running!',
        'endpoints': ['/extract-crypto-actions']
    })
