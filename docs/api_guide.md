# Yoink API Guide

The `yoink-api` service provides HTTP endpoints to sanitize code fragments or pack entire codebases remotely.

## Running the API Server

Start the API server using uvicorn:

```bash
# Starts the server on http://localhost:8000
python -m uvicorn yoink.api.main:app --reload
```

Interactive OpenAPI docs are available at:
*   Swagger UI: `http://localhost:8000/docs`
*   ReDoc: `http://localhost:8000/redoc`

---

## Endpoints

### 1. Sanitize Content
*   **Endpoint:** `POST /api/v1/sanitize`
*   **Description:** Clean comments, excess whitespace, mask secrets, and strip compliance patterns from a single code snippet payload.

**Request Body:**
```json
{
  "content": "def run():\n    # This is a secret key\n    api_key = \"AKIA1234567890ABCDEF\"\n    # Connect to local database\n    db_url = \"http://db.internal.net\"\n    return True",
  "file_extension": ".py",
  "strip_comments": true,
  "strip_whitespace": true,
  "mask_secrets": true,
  "custom_secrets": null,
  "compliance_patterns": {
    "\\b[a-zA-Z0-9.-]+\\.internal\\.net\\b": "[PROPRIETARY_ENDPOINT]"
  }
}
```

**Response:**
```json
{
  "sanitized_content": "def run():\n    api_key = <AWS_ACCESS_KEY>\n    db_url = \"http://[PROPRIETARY_ENDPOINT]\"\n    return True"
}
```

---

### 2. Pack Files
*   **Endpoint:** `POST /api/v1/pack`
*   **Description:** Accepts multiple file paths and contents directly to assemble them into a packed markdown document.

**Request Body:**
```json
{
  "files": [
    {
      "path": "main.py",
      "content": "import helper\n# Comment\nhelper.greet()"
    },
    {
      "path": "helper.py",
      "content": "def greet():\n    print('Hello')"
    }
  ],
  "strip_comments": true,
  "strip_whitespace": true,
  "mask_secrets": true,
  "custom_secrets": null,
  "compliance_patterns": {
    "\\bYoinkCorp\\b": "[COMPANY_NAME]"
  },
  "visualize": true
}
```

**Response:**
```json
{
  "total_files": 2,
  "packed_content": "# Yoink Codebase Pack\n..."
}
```

---

### 3. Pack ZIP
*   **Endpoint:** `POST /api/v1/pack-zip`
*   **Description:** Uploads a ZIP archive of a project and receives the packed markdown. If a `.yoinkconfig.json` is present in the ZIP root, it will be automatically read and applied for scanner excludes, secret masking, and compliance stripping patterns.
*   **Content-Type:** `multipart/form-data`

**Parameters:**
*   `zip_file`: File (Binary ZIP)
*   `strip_comments`: bool (default: true)
*   `strip_whitespace`: bool (default: true)
*   `mask_secrets`: bool (default: true)
*   `visualize`: bool (default: true)
