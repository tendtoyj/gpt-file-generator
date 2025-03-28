from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/generate-txt', methods=['POST'])
def generate_txt():
    data = request.get_json()
    content = data.get('content', '')
    filename = data.get('filename', 'gpt_output.txt')
    
    # Create directory for files if it doesn't exist
    os.makedirs('files', exist_ok=True)
    
    # Save content to file
    filepath = os.path.join('files', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Generate a proper URL for downloading
    base_url = request.host_url.rstrip('/')
    download_url = f"{base_url}/download/{filename}"
    
    return jsonify({
        'downloadUrl': download_url
    })

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory('files', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
