from flask import Flask, request, jsonify, send_from_directory
import os
import logging
import traceback
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 모든 요청에 대한 로깅 미들웨어
@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())
    logger.debug('URL: %s %s', request.method, request.url)

# 모든 응답에 대한 로깅 미들웨어
@app.after_request
def log_response_info(response):
    logger.debug('Response Status: %s', response.status)
    logger.debug('Response: %s', response.get_data())
    return response

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "running",
        "message": "Text File Generator API is running. Use /generate-txt endpoint for file generation."
    })

@app.route('/generate-txt', methods=['POST'])
def generate_txt():
    try:
        logger.info('Received request to generate txt file')
        
        # 요청 내용 로깅
        if not request.is_json:
            logger.error('Request is not JSON: %s', request.get_data())
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        logger.debug('Request data: %s', data)
        
        content = data.get('content', '')
        if not content:
            logger.warning('Empty content received')
            
        filename = data.get('filename', 'gpt_output.txt')
        logger.info('Generating file: %s', filename)
        
        # Create directory for files if it doesn't exist
        os.makedirs('files', exist_ok=True)
        logger.debug('Created directory: files')
        
        # Save content to file
        filepath = os.path.join('files', filename)
        logger.debug('File path: %s', filepath)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info('File written successfully')
        
        # Generate a proper URL for downloading
        base_url = request.host_url.rstrip('/')
        download_url = f"{base_url}/download/{filename}"
        logger.info('Generated download URL: %s', download_url)
        
        return jsonify({
            'downloadUrl': download_url
        })
    except Exception as e:
        logger.error('Error in generate_txt: %s', str(e))
        logger.error('Traceback: %s', traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        logger.info('Download requested for file: %s', filename)
        # 파일 경로 확인
        file_path = os.path.join('files', filename)
        if not os.path.exists(file_path):
            logger.error('File not found: %s', file_path)
            return jsonify({'error': 'File not found'}), 404
            
        # 파일 내용 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        # 응답 생성
        response = app.response_class(
            response=file_content,
            status=200,
            mimetype='text/plain'
        )
        response.headers.set('Content-Disposition', f'attachment; filename={filename}')
        return response
    except Exception as e:
        logger.error('Error in download_file: %s', str(e))
        logger.error('Traceback: %s', traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# 오류 핸들러 추가
@app.errorhandler(404)
def not_found(e):
    logger.warning('404 error: %s', request.url)
    return jsonify({"error": "Not found", "path": request.path}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error('500 error: %s', str(e))
    return jsonify({"error": "Server error", "details": str(e)}), 500

if __name__ == '__main__':
    logger.info('Starting server on port 10000')
    try:
        app.run(host='0.0.0.0', port=10000, debug=True)
    except Exception as e:
        logger.critical('Failed to start server: %s', str(e))
        logger.critical('Traceback: %s', traceback.format_exc())
