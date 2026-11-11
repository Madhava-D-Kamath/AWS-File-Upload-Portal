# ☁️ AWS File Upload Portal

A cloud-based file upload application built using **Python Flask** and deployed on **Amazon EC2**. Uploaded files are stored in Amazon S3, file metadata is saved in Amazon DynamoDB, and users receive confirmation emails through Amazon SES.

## 🌐 Live Application

| Detail | Value |
|---|---|
| Application Name | AWS File Upload Portal |
| EC2 Public IP | `3.25.93.135` |
| Application URL | http://3.25.93.135 |
| Hosting Platform | Amazon EC2 |
| Operating System | Amazon Linux 2023 |
| Web Server | Nginx |
| Backend | Flask + Gunicorn |
| Protocol | HTTP |

> **Note:** `3.25.93.135` is the last recorded EC2 public IP. Verify that it is still assigned to your instance. If the instance is stopped and restarted, its public IP may change unless an Elastic IP is configured. HTTPS is not configured yet.

## 1. 🏗️ Project Architecture

```text
                 User Browser
                      |
                      | HTTP (Port 80)
                      |
                      v
              Amazon EC2 Instance
                Amazon Linux 2023
                      |
                    Nginx
                 Port 80
                      |
                      v
              Gunicorn Application
                127.0.0.1:5000
                      |
                  Flask App
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Amazon S3  DynamoDB    Amazon SES
       File       Metadata    Email
       Storage    Storage     Notification
```

## 2. ☁️ AWS Infrastructure Details

| Component | Actual Configuration |
|---|---|
| Cloud Provider | Amazon Web Services (AWS) |
| AWS Region | Asia Pacific (Sydney) |
| Region Code | `ap-southeast-2` |
| EC2 Instance | `i-0b804cc0a1c330040` |
| Instance Type | `t3.micro` |
| Operating System | Amazon Linux 2023 |
| Web Server | Nginx |
| Application Server | Gunicorn |
| Backend Framework | Python Flask |
| Application Port | 5000 (localhost) |
| Public Web Port | 80 (HTTP) |

## 3. 🪣 Amazon S3 Configuration

| Setting | Actual Value |
|---|---|
| Bucket Name | `kamath-s3-aws-2026` |
| Region | `ap-southeast-2` |
| Public Access | Blocked |
| Versioning | Enabled |
| Encryption | SSE-S3 |
| Access Method | EC2 IAM Role |

Uploaded files are stored in Amazon S3 using date-based folders and unique filenames.

Example:

```text
uploads/
    2026-11-11/
        52aa9fc0_MDK_RESUME.pdf
        63c5383b_Smart_Meter.pdf
```

## 4. 🗄️ Amazon DynamoDB Configuration

| Setting | Actual Value |
|---|---|
| Table Name | `FileUploads` |
| Region | `ap-southeast-2` |
| Partition Key | `RecordId` |
| Key Type | String |
| Billing Mode | On-Demand (PAY_PER_REQUEST) |
| Status | ACTIVE |

The table stores upload information, including:

- Record ID
- User name
- Email address
- Original filename
- S3 object key
- File size
- Upload timestamp

## 5. 📧 Amazon SES Configuration

Amazon Simple Email Service is integrated to send upload confirmation emails.

| Setting | Actual Value |
|---|---|
| Service | Amazon SES |
| Region | `ap-southeast-2` |
| Verified Sender | `kamathmadhava81@gmail.com` |
| Account Status | Sandbox |

**Note:** The SES account is in Sandbox mode. Email sending is restricted to verified recipient addresses. Production access is required to send emails to arbitrary recipients.

## 6. 🔐 IAM Configuration

An IAM role is attached to the EC2 instance.

| IAM Component | Name |
|---|---|
| IAM Role | `EC2-FileUpload-Role` |
| IAM Policy | `EC2-FileUpload-Policy` |

The policy grants the application permissions to:

- Upload, download, list and delete S3 objects.
- Insert, retrieve, update and delete DynamoDB records.
- Send email notifications through SES.

The application uses the EC2 IAM role to access AWS services without storing AWS access keys in the project.

## 7. 💻 EC2 Application Configuration

The application is deployed at:

```text
/home/ec2-user/AWS-File-Upload/AWS-File-Upload-App-main
```

### Project Structure

```text
AWS-File-Upload-App-main/
│
├── app.py
├── requirements.txt
├── README.md
├── STEP_BY_STEP_GUIDE.txt
├── nginx.conf
├── flask-app.service
│
├── templates/
│   └── index.html
│
├── .gitignore
│
├── .env       (local configuration - not committed)
└── venv/      (Python virtual environment - not committed)
```

**Security:** `.env` and `venv/` are excluded from GitHub using `.gitignore`. Never upload actual environment configuration, AWS credentials or personal access tokens.

### Environment Configuration

The application uses the following environment variables:

```env
AWS_REGION=ap-southeast-2
S3_BUCKET_NAME=kamath-s3-aws-2026
DYNAMODB_TABLE=FileUploads
SES_SENDER_EMAIL=kamathmadhava81@gmail.com
```

These values are configured locally on the EC2 instance.

## 8. ⚙️ Application Server

Gunicorn runs the Flask application using:

```bash
gunicorn --workers 3 --bind 127.0.0.1:5000 --timeout 120 app:app
```

The application is managed through systemd:

```bash
sudo systemctl status flask-app
sudo systemctl restart flask-app
sudo systemctl enable flask-app
```

## 9. 🌐 Nginx Configuration

Nginx acts as a reverse proxy and forwards incoming HTTP requests to Gunicorn.

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 120s;
        proxy_connect_timeout 60s;
    }
}
```

Useful commands:

```bash
sudo systemctl status nginx
sudo systemctl restart nginx
sudo nginx -t
```

## 10. 🛡️ Security Group Configuration

| Type | Protocol | Port | Access |
|---|---|---|---|
| HTTP | TCP | 80 | `0.0.0.0/0` |
| SSH | TCP | 22 | EC2 Instance Connect managed prefix list |

The S3 bucket remains private. Access to AWS services is controlled through IAM permissions.

## 11. 🔄 Application Workflow

1. A user opens the file upload portal in a web browser.
2. The user enters their name and email address.
3. The user selects a file and clicks Upload.
4. Flask receives the uploaded file.
5. The file is uploaded to Amazon S3.
6. Upload metadata is saved in Amazon DynamoDB.
7. Amazon SES sends a confirmation email.
8. The user receives an upload confirmation.

## 12. ✅ Deployment Verification

The following components were tested during deployment:

| Component | Verification |
|---|---|
| EC2 | Instance launched and running |
| Python Flask | Application running |
| Gunicorn | Three workers running |
| Nginx | Active and running |
| S3 | File uploads confirmed |
| DynamoDB | Metadata records confirmed |
| IAM Role | EC2 role credentials detected |
| SES | Confirmation email successfully received |

The application returned HTTP 200 when tested locally through Nginx.

## 13. 📂 GitHub Repository

**Source Code Repository:**

https://github.com/Madhava-D-Kamath/AWS-File-Upload-Portal

## 14. 🛠️ Technologies Used

- Python
- Flask
- Gunicorn
- Nginx
- Amazon EC2
- Amazon S3
- Amazon DynamoDB
- Amazon SES
- AWS IAM
- Linux
- Git and GitHub

## 15. 🚀 Future Improvements

- Configure HTTPS using SSL/TLS.
- Connect a custom domain.
- Request Amazon SES production access.
- Add user authentication.
- Add file download and deletion functionality.
- Improve application monitoring and logging.
- Implement automated deployment using CI/CD.

---

## Project Information

**Project:** AWS File Upload Portal

**Deployment Platform:** Amazon Web Services

**Application:** Python Flask + Nginx + Gunicorn

**Region:** Asia Pacific (Sydney) — `ap-southeast-2`

**GitHub:** Madhava-D-Kamath
