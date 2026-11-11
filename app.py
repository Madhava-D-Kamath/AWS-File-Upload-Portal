import os
import uuid
import boto3
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── AWS Config (loaded from .env) ────────────────────────────────────────────
AWS_REGION        = os.environ.get('AWS_REGION', 'ap-south-1')
S3_BUCKET_NAME    = os.environ.get('S3_BUCKET_NAME', 'aws-batch-uploads-2024')
DYNAMODB_TABLE    = os.environ.get('DYNAMODB_TABLE', 'FileUploads')
SES_SENDER_EMAIL  = os.environ.get('SES_SENDER_EMAIL', '')   # Must be verified in SES

# ─── AWS Clients (uses IAM Role attached to EC2 — no keys needed) ─────────────
s3_client       = boto3.client('s3', region_name=AWS_REGION)
dynamodb        = boto3.resource('dynamodb', region_name=AWS_REGION)
ses_client      = boto3.client('ses', region_name=AWS_REGION)
table           = dynamodb.Table(DYNAMODB_TABLE)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'docx', 'xlsx', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_s3(file_obj, filename, content_type):
    """Upload file to S3 under uploads/YYYY-MM-DD/ prefix."""
    date_prefix = datetime.utcnow().strftime('%Y-%m-%d')
    unique_id   = str(uuid.uuid4())[:8]
    s3_key      = f"uploads/{date_prefix}/{unique_id}_{filename}"
    try:
        s3_client.upload_fileobj(
            file_obj,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256'
            }
        )
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        logger.info(f"Uploaded to S3: {s3_key}")
        return s3_key, s3_url
    except ClientError as e:
        logger.error(f"S3 upload error: {e}")
        raise

def save_to_dynamodb(record_id, name, email, filename, s3_key, file_size):
    """Save upload metadata to DynamoDB."""
    try:
        table.put_item(Item={
            'RecordId':  record_id,
            'Name':      name,
            'Email':     email,
            'FileName':  filename,
            'S3Key':     s3_key,
            'FileSize':  str(file_size),
            'Timestamp': datetime.utcnow().isoformat(),
            'Status':    'completed'
        })
        logger.info(f"Saved record {record_id} to DynamoDB")
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        raise

def send_confirmation_email(to_email, name, filename, upload_time):
    """Send a beautiful HTML confirmation email via SES."""
    if not SES_SENDER_EMAIL:
        logger.warning("SES_SENDER_EMAIL not set — skipping email.")
        return False
    subject = f"Your file '{filename}' was uploaded successfully!"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f7fb; margin: 0; padding: 0; }}
        .container {{ max-width: 580px; margin: 40px auto; background: #fff; border-radius: 12px;
                      box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
                   padding: 36px 40px; text-align: center; }}
        .header h1 {{ color: #fff; margin: 0; font-size: 24px; font-weight: 700; }}
        .header p  {{ color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px; }}
        .body  {{ padding: 36px 40px; }}
        .body p {{ color: #333; font-size: 15px; line-height: 1.7; margin: 0 0 16px; }}
        .info-box {{ background: #f0f6ff; border-left: 4px solid #1a73e8; border-radius: 6px;
                     padding: 16px 20px; margin: 24px 0; }}
        .info-box p {{ margin: 4px 0; font-size: 14px; color: #444; }}
        .info-box strong {{ color: #1a73e8; }}
        .badge {{ display: inline-block; background: #e8f5e9; color: #2e7d32;
                  border-radius: 20px; padding: 6px 16px; font-size: 13px;
                  font-weight: 600; margin-top: 8px; }}
        .footer {{ background: #f4f7fb; padding: 20px 40px; text-align: center;
                   font-size: 12px; color: #888; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>&#x2705; Upload Successful!</h1>
          <p>Your file has been securely stored on AWS S3</p>
        </div>
        <div class="body">
          <p>Hello <strong>{name}</strong>,</p>
          <p>We have successfully received your file upload. Here are your upload details:</p>
          <div class="info-box">
            <p><strong>File Name:</strong> {filename}</p>
            <p><strong>Upload Time:</strong> {upload_time}</p>
            <p><strong>Storage:</strong> Amazon S3 (Encrypted)</p>
          </div>
          <span class="badge">&#x1F512; Securely Encrypted &nbsp;|&nbsp; &#x2601; Stored on AWS S3</span>
          <p style="margin-top:24px;">Your file is stored securely. No further action is needed.</p>
        </div>
        <div class="footer">
          <p>This is an automated email from the AWS Batch Student Project.</p>
          <p>Powered by Amazon EC2 &bull; Amazon S3 &bull; Amazon SES &bull; Amazon DynamoDB</p>
        </div>
      </div>
    </body>
    </html>
    """
    text_body = f"Hello {name},\n\nYour file '{filename}' was uploaded successfully at {upload_time}.\n\nThank you!"
    try:
        ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': text_body,  'Charset': 'UTF-8'},
                    'Html': {'Data': html_body,  'Charset': 'UTF-8'}
                }
            }
        )
        logger.info(f"Confirmation email sent to {to_email}")
        return True
    except ClientError as e:
        logger.error(f"SES error: {e}")
        return False

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    name    = request.form.get('name', '').strip()
    email   = request.form.get('email', '').strip()
    file    = request.files.get('file')

    # Validation
    if not name or not email:
        return jsonify({'success': False, 'message': 'Name and email are required.'}), 400
    if not file or file.filename == '':
        return jsonify({'success': False, 'message': 'Please select a file.'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        record_id    = str(uuid.uuid4())
        filename     = file.filename
        content_type = file.content_type or 'application/octet-stream'
        file_data    = file.read()
        file_size    = len(file_data)
        file.seek(0)

        # 1. Upload to S3
        s3_key, s3_url = upload_to_s3(file, filename, content_type)

        # 2. Save to DynamoDB
        upload_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        save_to_dynamodb(record_id, name, email, filename, s3_key, file_size)

        # 3. Send confirmation email via SES
        email_sent = send_confirmation_email(email, name, filename, upload_time)

        return jsonify({
            'success':    True,
            'message':    f'File uploaded successfully! {"Confirmation email sent." if email_sent else ""}',
            'record_id':  record_id,
            'filename':   filename,
            'size_kb':    round(file_size / 1024, 2)
        })

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({'success': False, 'message': 'Upload failed. Please try again.'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
