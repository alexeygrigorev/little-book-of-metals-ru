#!/usr/bin/env python3
"""
eBook Builder for "Удивительный мир металлов"

This script assembles the book from all sections and chapters, generates a Table of Contents,
and converts the content to EPUB and MOBI formats using Pandoc and Calibre.

Usage:
    python build_book.py [output_directory]

Requirements:
    - pandoc (for EPUB generation)
    - calibre (ebook-convert command for MOBI generation)

The script will:
1. Discover all sections (часть_*) and their chapters (глава_*.md)
2. Assemble content starting with section README, then chapters in order
3. Generate a Table of Contents
4. Use images/cover.jpg as book cover if present
5. Create EPUB using Pandoc
6. Create MOBI using Calibre (ebook-convert)

Author: GitHub Copilot Assistant
"""

import os
import sys
import subprocess
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import tempfile
import yaml


class BookBuilder:
    def __init__(self, repo_root: Path, output_dir: Path):
        self.repo_root = Path(repo_root)
        self.output_dir = Path(output_dir)
        self.temp_dir = None
        
        # Book metadata
        self.title = "Удивительный мир металлов"
        self.subtitle = "Книга для подростков о металлах и металлургии"
        self.author = "Автор"
        self.language = "ru"
        
    def __enter__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="book_assembly_"))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def check_dependencies(self) -> bool:
        """Check if required tools are available."""
        try:
            subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
            print("✓ Pandoc is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ Pandoc is not available. Please install pandoc.")
            return False
            
        try:
            subprocess.run(["ebook-convert", "--version"], capture_output=True, check=True)
            print("✓ Calibre (ebook-convert) is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ Calibre is not available. Please install calibre.")
            return False
            
        return True
    
    def discover_sections(self) -> List[Tuple[str, Path]]:
        """Discover all section directories and return them sorted."""
        sections = []
        
        for item in self.repo_root.iterdir():
            if item.is_dir() and item.name.startswith("часть_"):
                sections.append((item.name, item))
        
        # Sort by section number
        sections.sort(key=lambda x: self._extract_section_number(x[0]))
        print(f"Found {len(sections)} sections: {[s[0] for s in sections]}")
        return sections
    
    def _extract_section_number(self, section_name: str) -> int:
        """Extract section number from directory name."""
        match = re.search(r'часть_(\d+)', section_name)
        return int(match.group(1)) if match else 0
    
    def discover_chapters(self, section_path: Path) -> List[Tuple[str, Path]]:
        """Discover all chapter files in a section directory."""
        chapters = []
        
        for item in section_path.iterdir():
            if item.is_file() and item.name.startswith("глава_") and item.name.endswith(".md"):
                chapters.append((item.name, item))
        
        # Sort by chapter number
        chapters.sort(key=lambda x: self._extract_chapter_number(x[0]))
        return chapters
    
    def _extract_chapter_number(self, chapter_name: str) -> int:
        """Extract chapter number from filename."""
        match = re.search(r'глава_(\d+)', chapter_name)
        return int(match.group(1)) if match else 0
    
    def extract_title(self, markdown_file: Path) -> str:
        """Extract title from markdown file."""
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip YAML front matter if present
            if content.startswith('---\n'):
                parts = content.split('---\n', 2)
                if len(parts) >= 3:
                    content = parts[2]
            
            # Find first H1 heading
            match = re.search(r'^# (.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
            
            # Fallback to filename
            return markdown_file.stem.replace('_', ' ')
            
        except Exception as e:
            print(f"Warning: Could not extract title from {markdown_file}: {e}")
            return markdown_file.stem.replace('_', ' ')
    
    def strip_yaml_frontmatter(self, content: str) -> str:
        """Remove YAML front matter from markdown content."""
        if content.startswith('---\n'):
            parts = content.split('---\n', 2)
            if len(parts) >= 3:
                return parts[2].lstrip('\n')
        return content
    
    def generate_toc(self, sections: List[Tuple[str, Path]]) -> str:
        """Generate Table of Contents."""
        toc = "## Содержание\n\n"
        
        for section_name, section_path in sections:
            # Get section title
            readme_path = section_path / "README.md"
            if readme_path.exists():
                section_title = self.extract_title(readme_path)
                toc += f"### {section_title}\n\n"
                
                # List chapters
                chapters = self.discover_chapters(section_path)
                for chapter_name, chapter_path in chapters:
                    chapter_title = self.extract_title(chapter_path)
                    toc += f"- {chapter_title}\n"
                
                toc += "\n"
        
        return toc
    
    def assemble_book_content(self) -> str:
        """Assemble the complete book content."""
        print("Assembling book content...")
        
        # Start with main title and description
        content = f"# {self.title}\n"
        content += f"## {self.subtitle}\n\n"
        
        # Add main description from README if available
        main_readme = self.repo_root / "README.md"
        if main_readme.exists():
            with open(main_readme, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Extract description (skip title and TOC)
            lines = readme_content.split('\n')
            description_lines = []
            in_description = False
            
            for line in lines:
                if line.strip().startswith('<img src="./images/cover.jpg"'):
                    in_description = True
                    continue
                elif line.strip().startswith('## Полное содержание') or line.strip().startswith('## О проекте'):
                    break
                elif in_description and line.strip():
                    description_lines.append(line)
            
            if description_lines:
                content += '\n'.join(description_lines) + "\n\n"
        
        # Discover sections
        sections = self.discover_sections()
        
        # Generate and add TOC
        toc = self.generate_toc(sections)
        content += toc + "\n---\n\n"
        
        # Process each section
        for section_name, section_path in sections:
            print(f"Processing section: {section_name}")
            
            # Add section README content
            readme_path = section_path / "README.md"
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                # Remove front matter and add content
                readme_content = self.strip_yaml_frontmatter(readme_content)
                content += readme_content + "\n\n---\n\n"
            
            # Add all chapters in order
            chapters = self.discover_chapters(section_path)
            for chapter_name, chapter_path in chapters:
                print(f"  Adding chapter: {chapter_name}")
                
                with open(chapter_path, 'r', encoding='utf-8') as f:
                    chapter_content = f.read()
                
                # Remove front matter and add content
                chapter_content = self.strip_yaml_frontmatter(chapter_content)
                content += chapter_content + "\n\n---\n\n"
        
        return content
    
    def create_metadata_file(self) -> Path:
        """Create Pandoc metadata file."""
        metadata = {
            'title': self.title,
            'subtitle': self.subtitle,
            'author': self.author,
            'language': self.language,
            'subject': "Металлургия, Химия, Наука",
            'description': "Увлекательное путешествие по миру металлов - от истории металлургии до современных технологий"
        }
        
        metadata_file = self.temp_dir / "metadata.yaml"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write("---\n")
            yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False)
            f.write("---\n")
        
        return metadata_file
    
    def build_epub(self, content: str) -> Path:
        """Build EPUB file using Pandoc."""
        print("Generating EPUB...")
        
        # Write content to temporary file
        content_file = self.temp_dir / "book.md"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create metadata file
        metadata_file = self.create_metadata_file()
        
        # Output file
        epub_file = self.temp_dir / "little-book-of-metals-ru.epub"
        
        # Build pandoc command
        cmd = [
            "pandoc",
            str(content_file),
            f"--metadata-file={metadata_file}",
            "--from=markdown",
            "--to=epub3",
            f"--output={epub_file}",
            "--toc",
            "--toc-depth=2",
            "--split-level=1"
        ]
        
        # Add cover if available
        cover_path = self.repo_root / "images" / "cover.jpg"
        if cover_path.exists():
            cmd.extend([f"--epub-cover-image={cover_path}"])
            print(f"Using cover image: {cover_path}")
        
        # Run pandoc
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✓ EPUB generated successfully")
            return epub_file
        except subprocess.CalledProcessError as e:
            print(f"✗ EPUB generation failed: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            raise
    
    def build_mobi(self, epub_file: Path) -> Path:
        """Build MOBI file using Calibre."""
        print("Generating MOBI...")
        
        mobi_file = self.temp_dir / "little-book-of-metals-ru.mobi"
        
        cmd = [
            "ebook-convert",
            str(epub_file),
            str(mobi_file),
            f"--title={self.title}",
            f"--authors={self.author}",
            f"--language={self.language}",
            "--book-producer=Python Build Script",
            "--publisher=GitHub",
            f"--comments={self.subtitle}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✓ MOBI generated successfully")
            return mobi_file
        except subprocess.CalledProcessError as e:
            print(f"✗ MOBI generation failed: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            raise
    
    def build(self) -> Dict[str, Path]:
        """Build the complete eBook."""
        print(f"Building eBook in repository: {self.repo_root}")
        print(f"Output directory: {self.output_dir}")
        
        # Check dependencies
        if not self.check_dependencies():
            raise RuntimeError("Required dependencies are not available")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Assemble book content
        content = self.assemble_book_content()
        
        # Save assembled markdown for reference
        markdown_file = self.temp_dir / "complete-book.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Book content assembled: {len(content.split())} words")
        
        # Build formats
        epub_file = self.build_epub(content)
        mobi_file = self.build_mobi(epub_file)
        
        # Copy to output directory
        output_files = {}
        
        final_epub = self.output_dir / epub_file.name
        shutil.copy2(epub_file, final_epub)
        output_files['epub'] = final_epub
        
        final_mobi = self.output_dir / mobi_file.name
        shutil.copy2(mobi_file, final_mobi)
        output_files['mobi'] = final_mobi
        
        final_markdown = self.output_dir / markdown_file.name
        shutil.copy2(markdown_file, final_markdown)
        output_files['markdown'] = final_markdown
        
        print(f"\n✓ Build completed successfully!")
        print(f"  EPUB: {final_epub}")
        print(f"  MOBI: {final_mobi}")
        print(f"  Markdown: {final_markdown}")
        
        return output_files


def main():
    """Main entry point."""
    # Parse command line arguments
    if len(sys.argv) > 2:
        print("Usage: python build_book.py [output_directory]")
        sys.exit(1)
    
    # Determine paths
    repo_root = Path(__file__).parent
    output_dir = Path(sys.argv[1]) if len(sys.argv) == 2 else repo_root / "dist"
    
    try:
        with BookBuilder(repo_root, output_dir) as builder:
            output_files = builder.build()
            
        print(f"\nBuild completed successfully!")
        print(f"Output files:")
        for format_name, file_path in output_files.items():
            print(f"  {format_name.upper()}: {file_path}")
            
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()