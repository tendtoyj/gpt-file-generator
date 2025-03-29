from flask import Flask, request, jsonify, send_file
import os
import logging
import traceback
from datetime import datetime
import io
from urllib.parse import quote, unquote

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
    logger.debug('Headers: %s', dict(request.headers))
    logger.debug('URL: %s %s', request.method, request.url)
    if request.method == 'POST' and request.is_json:
        logger.debug('JSON Body: %s', request.json)

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
        
        # 요청 데이터 검증
        if not request.is_json:
            logger.error('Request is not JSON')
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        
        content = data.get('content')
        if not content:
            logger.warning('Empty or missing content')
            return jsonify({'error': 'Content is required'}), 400
            
        filename = data.get('filename', 'gpt_output.txt')
        if not filename.endswith('.txt'):
            filename += '.txt'
        logger.info(f'Generating file: {filename}')
        
        # 콘텐츠 크기 제한 추가 (예: 10MB)
        if len(content) > 10 * 1024 * 1024:
            logger.warning('Content size exceeds limit')
            return jsonify({'error': 'Content size exceeds the limit (10MB)'}), 400
        
        # Create directory for files if it doesn't exist
        os.makedirs('files', exist_ok=True)
        
        # Save content to file
        filepath = os.path.join('files', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f'File written successfully: {filepath}')
        
        # 항상 HTTPS URL 생성 (URL 인코딩 적용)
        host = request.headers.get('Host', 'gpt-file-api.onrender.com')
        encoded_filename = quote(filename)
        download_url = f"https://{host}/download/{encoded_filename}"
        logger.info(f'Generated download URL: {download_url}')
        
        return jsonify({
            'downloadUrl': download_url
        })
    except Exception as e:
        logger.error(f'Error in generate_txt: {str(e)}')
        logger.error(f'Traceback: {traceback.format_exc()}')
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        logger.info(f'Download requested for encoded file: {filename}')
        
        # 경로 탐색 방지
        if os.path.sep in filename or '..' in filename:
            logger.error(f'Invalid filename: {filename}')
            return jsonify({'error': 'Invalid filename'}), 400
            
        # URL 디코딩
        decoded_filename = unquote(filename)
        logger.info(f'Decoded filename: {decoded_filename}')
        
        file_path = os.path.join('files', decoded_filename)
        
        if not os.path.exists(file_path):
            logger.error(f'File not found: {file_path}')
            return jsonify({'error': 'File not found'}), 404
        
        # 바이너리 모드로 파일 읽기
        with open(file_path, 'rb') as f:
            buffer = io.BytesIO(f.read())
        buffer.seek(0)
        
        # 파일 다운로드로 전송
        return send_file(
            buffer,
            as_attachment=True,
            download_name=decoded_filename,
            mimetype='text/plain'
        )
    except Exception as e:
        logger.error(f'Error in download_file: {str(e)}')
        logger.error(f'Traceback: {traceback.format_exc()}')
        return jsonify({'error': str(e)}), 500

# 오류 핸들러
@app.errorhandler(404)
def not_found(e):
    logger.warning(f'404 error: {request.url}')
    return jsonify({"error": "Not found", "path": request.path}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f'500 error: {str(e)}')
    return jsonify({"error": "Server error", "details": str(e)}), 500

# 임시 파일 정리 함수 (필요에 따라 주기적으로 호출)
def cleanup_old_files(max_age_hours=24):
    files_dir = 'files'
    if not os.path.exists(files_dir):
        return
    
    current_time = datetime.now()
    for filename in os.listdir(files_dir):
        file_path = os.path.join(files_dir, filename)
        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        if (current_time - file_modified).total_seconds() > max_age_hours * 3600:
            try:
                os.remove(file_path)
                logger.info(f'Removed old file: {file_path}')
            except Exception as e:
                logger.error(f'Failed to remove file {file_path}: {str(e)}')

if __name__ == '__main__':
    logger.info('Starting server on port 10000')
    app.run(host='0.0.0.0', port=10000)
