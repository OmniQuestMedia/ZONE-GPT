import os
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import shutil

# Set test datasets directory before importing the app
TEST_DATA_DIR = "/tmp/test_datasets"
os.environ["DATASETS_DIR"] = TEST_DATA_DIR

# Add parent directory to path to import core modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.main import app, DATASETS_DIR

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data before and after each test"""
    # Setup: Clean before test
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
    
    yield
    
    # Teardown: Clean after test
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)

def test_upload_valid_csv():
    """Test uploading a valid CSV file"""
    csv_content = b"name,age,city\nJohn,30,NYC\nJane,25,LA"
    
    response = client.post(
        "/ingest/upload",
        files={"file": ("test_data.csv", csv_content, "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "path" in data
    assert "checksum" in data
    assert "size" in data
    assert data["message"] == "File uploaded successfully"
    assert data["size"] == len(csv_content)

def test_upload_non_csv_file():
    """Test uploading a non-CSV file"""
    txt_content = b"This is a text file"
    
    response = client.post(
        "/ingest/upload",
        files={"file": ("test_data.txt", txt_content, "text/plain")}
    )
    
    assert response.status_code == 400
    assert "Only .csv files are allowed" in response.json()["detail"]

def test_upload_non_utf8_file():
    """Test uploading a non-UTF-8 encoded file"""
    # Create content with invalid UTF-8 bytes
    invalid_utf8 = b"name,age\n\xff\xfe"
    
    response = client.post(
        "/ingest/upload",
        files={"file": ("test_data.csv", invalid_utf8, "text/csv")}
    )
    
    assert response.status_code == 400
    assert "File must be UTF-8 encoded" in response.json()["detail"]

def test_upload_csv_without_header():
    """Test uploading a CSV file without header"""
    empty_content = b""
    
    response = client.post(
        "/ingest/upload",
        files={"file": ("test_data.csv", empty_content, "text/csv")}
    )
    
    assert response.status_code == 400
    assert "header row" in response.json()["detail"].lower()

def test_upload_csv_with_empty_header():
    """Test uploading a CSV file with empty header"""
    empty_header = b",,"
    
    response = client.post(
        "/ingest/upload",
        files={"file": ("test_data.csv", empty_header, "text/csv")}
    )
    
    assert response.status_code == 400
    assert "valid header row" in response.json()["detail"].lower()

def test_upload_large_file():
    """Test uploading a file that exceeds maximum size"""
    # Create content larger than MAX_FILE_SIZE (10 MB)
    large_content = b"name,age\n" + b"x" * (11 * 1024 * 1024)
    
    response = client.post(
        "/ingest/upload",
        files={"file": ("large_data.csv", large_content, "text/csv")}
    )
    
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.json()["detail"]

def test_checksum_calculation():
    """Test that SHA256 checksum is correctly calculated"""
    import hashlib
    csv_content = b"id,name\n1,test"
    expected_checksum = hashlib.sha256(csv_content).hexdigest()
    
    response = client.post(
        "/ingest/upload",
        files={"file": ("test_data.csv", csv_content, "text/csv")}
    )
    
    assert response.status_code == 200
    assert response.json()["checksum"] == expected_checksum

def test_file_storage_structure():
    """Test that files are stored in correct directory structure"""
    csv_content = b"product,price\nlaptop,1000"
    
    response = client.post(
        "/ingest/upload",
        files={"file": ("inventory_data.csv", csv_content, "text/csv")}
    )
    
    assert response.status_code == 200
    path = response.json()["path"]
    
    # Verify path structure: <datasets_dir>/<name>/<version>.csv
    assert "inventory_data/v1.csv" in path
