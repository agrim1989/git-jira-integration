import os
import httpx
from pathlib import Path
from typing import List

class FileMerger:
    """
    Utility to download files from a list of URLs and merge them into a single file.
    """
    def __init__(self, temp_dir: str = "temp_downloads"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url: str) -> str:
        """Download a single file and return the local path."""
        local_filename = url.split('/')[-1]
        local_path = self.temp_dir / local_filename
        
        print(f"Downloading {url} to {local_path}...")
        with httpx.Client(follow_redirects=True) as client:
            with client.stream("GET", url) as r:
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_bytes(chunk_size=8192):
                        f.write(chunk)
        return str(local_path)

    def merge_files(self, file_paths: List[str], output_file: str):
        """Merge multiple files into one."""
        print(f"Merging {len(file_paths)} files into {output_file}...")
        with open(output_file, 'wb') as outfile:
            for fname in file_paths:
                if not os.path.exists(fname):
                    print(f"Warning: File {fname} not found. Skipping.")
                    continue
                with open(fname, 'rb') as infile:
                    outfile.write(infile.read())
                    outfile.write(b"\n") # separator
        print("Merge complete.")

    def cleanup(self):
        """Remove temporary files."""
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("*"):
                file.unlink()
            self.temp_dir.rmdir()
            print(f"Cleaned up {self.temp_dir}")

def process_file_list(urls: List[str], output_filename: str):
    """Orchestrate the download and merge process."""
    merger = FileMerger()
    downloaded_paths = []
    
    try:
        for url in urls:
            if url.startswith(("http://", "https://")):
                path = merger.download_file(url)
                downloaded_paths.append(path)
            else:
                downloaded_paths.append(url)
        
        merger.merge_files(downloaded_paths, output_filename)
    finally:
        # Only cleanup if they were downloaded
        downloaded_only = [p for p in downloaded_paths if str(merger.temp_dir) in p]
        # For now, let's just cleanup the whole temp dir
        merger.cleanup()

if __name__ == "__main__":
    # Example usage
    sample_urls = [
        "https://raw.githubusercontent.com/agrim1989/git-jira-mcp-integration/main/README.md",
        "https://raw.githubusercontent.com/agrim1989/git-jira-mcp-integration/main/requirements.txt"
    ]
    process_file_list(sample_urls, "merged_output.txt")
