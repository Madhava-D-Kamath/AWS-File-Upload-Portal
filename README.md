# AWS File Upload App — Deployment Guide

## Architecture
User Browser → EC2 (Flask + Nginx) → S3 (files) + DynamoDB (metadata) + SES (email)

## Files in this zip
- app.py               — Main Flask application
- templates/index.html — Web UI
- requirements.txt     — Python dependencies
- .env                 — Environment config (edit this!)
- nginx.conf           — Nginx reverse proxy config
- flask-app.service    — Systemd service file

## Quick Start (on EC2)
See STEP_BY_STEP_GUIDE.txt for the complete AWS Console + EC2 setup instructions.

## After deploying
Access the app at: http://<EC2-Public-IP>
🏗️ What We're Building
A web application where users:

Enter their Name and Email
Select a file/image from their laptop
Click Upload
The file gets stored in Amazon S3
The metadata (name, email, filename, timestamp) gets stored in Amazon DynamoDB
A confirmation email is sent via Amazon SES

🛠️ AWS Services Involved
Service									Role
EC2 (Amazon Linux 2023, t2.medium)	Hosts the Python Flask web app
S3										Stores the uploaded files/images
DynamoDB								Stores metadata (name, email, file name, upload time)
SES (Simple Email Service)				Sends confirmation email to the user
IAM									Permissions — EC2 talks to S3, DynamoDB, SES
Security Groups							Firewall rules for EC2 (port 80, 22)
GitHub									Source code storage (as you requested)
________________________________________
🏛️ Architecture Flow
User Browser
    │
    ▼
EC2 (Flask App, port 80)
    │
    ├──► S3 Bucket          (stores the uploaded file)
    ├──► DynamoDB Table      (stores name, email, filename, timestamp)
    └──► SES                 (sends confirmation email)

🪣 S3 Bucket Details
Setting				Value
Bucket Name		aws-batch-uploads-2024
Region				ap-south-1 (Mumbai — closest to you)
Public Access		❌ Blocked (private bucket)
Versioning			✅ Enabled (good practice)
Encryption			✅ SSE-S3 (server-side encryption)
Access Method		Via IAM Role attached to EC2 (no access keys needed)


