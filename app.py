from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/api/generate-txt', methods=['POST'])
def generate_txt():
    data = request.get_json()
    content = data.get('content', '')
    filename = data.get('filename', 'gpt_output.txt')

    os.makedirs('files', exist_ok=True)
    filepath = f'files/{filename}'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return jsonify({
        'downloadUrl': f'https://your-domain.onrender.com/{filepath}'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
