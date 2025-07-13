# File_integrity

This project provides a secure and efficient way to verify file integrity using cryptographic hashing algorithms like SHA-256 and MD5. It is built with FastAPI, offering a lightweight yet powerful solution to detect unauthorized file modifications. The API allows users to generate hashes for uploaded files and validate them against precomputed checksums, ensuring data authenticity and security. Ideal for applications requiring tamper-proof file verification, such as secure document storage, software distribution, or system monitoring, this tool delivers a reliable and easy-to-integrate solution.

Key Features

Generate cryptographic hashes for files using supported algorithms (SHA-256, MD5).

Validate file integrity by comparing computed hashes with provided checksums.

Interactive API documentation via Swagger UI for easy testing and integration.

Lightweight and fast, leveraging FastAPI’s asynchronous capabilities.

Project Structure
The repository is organized as follows:

main.py: Contains the core FastAPI application and endpoint logic.

requirements.txt: Lists all project dependencies.

venv/: Stores the virtual environment (excluded from version control).

.gitignore: Specifies files and directories to ignore (e.g., venv/, __pycache__/).
