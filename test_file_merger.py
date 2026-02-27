import unittest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path
from file_merger import FileMerger

class TestFileMerger(unittest.TestCase):
    def setUp(self):
        self.merger = FileMerger(temp_dir="test_temp")
        self.test_output = "test_merged.txt"

    def tearDown(self):
        if os.path.exists(self.test_output):
            os.remove(self.test_output)
        if Path("test_temp").exists():
            for f in Path("test_temp").glob("*"):
                f.unlink()
            Path("test_temp").rmdir()

    @patch('httpx.Client')
    def test_download_file(self, mock_client_class):
        # Mocking the download
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_bytes.return_value = [b"content chunk"]
        mock_client.stream.return_value.__enter__.return_value = mock_response
        
        url = "http://example.com/test.txt"
        path = self.merger.download_file(url)
        
        self.assertTrue(os.path.exists(path))
        with open(path, 'rb') as f:
            self.assertEqual(f.read(), b"content chunk")

    def test_merge_files(self):
        # Create dummy files
        f1 = Path("test_temp/f1.txt")
        f2 = Path("test_temp/f2.txt")
        f1.parent.mkdir(parents=True, exist_ok=True)
        
        with open(f1, 'w') as f: f.write("file1")
        with open(f2, 'w') as f: f.write("file2")
        
        self.merger.merge_files([str(f1), str(f2)], self.test_output)
        
        self.assertTrue(os.path.exists(self.test_output))
        with open(self.test_output, 'r') as f:
            content = f.read()
            self.assertIn("file1", content)
            self.assertIn("file2", content)

if __name__ == '__main__':
    unittest.main()
