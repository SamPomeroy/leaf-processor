#!/usr/bin/env python3
"""
XLSX to CSV Converter for Banyan Labs Perfect Processor
Converts Excel files to CSV format compatible with perfect_processor.py
Preserves all data and handles multiple sheet scenarios
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import argparse
from datetime import datetime
import json
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class XLSXToCSVConverter:
    """Convert XLSX files to CSV format compatible with perfect_processor.py"""
    
    def __init__(self, input_dir: str = "data/xlsx_raw", output_dir: str = "data/csv_raw"):
        """
        Initialize the converter
        
        Args:
            input_dir: Directory containing XLSX files
            output_dir: Directory to save CSV files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track conversion statistics
        self.stats = {
            'files_processed': 0,
            'sheets_processed': 0,
            'total_rows': 0,
            'total_columns': 0,
            'contacts_with_email': 0,
            'contacts_with_phone': 0,
            'errors': []
        }
        
        # Column mappings that perfect_processor.py expects
        # Based on the enhanced_lead_discovery and intelligent_csv_mapping functions
        self.standard_columns = {
            # Name columns (perfect processor looks for these)
            'name': ['Contact Full Name', 'Full Name', 'Name', 'contact_name', 'name'],
            
            # Email columns (perfect processor pattern)
            'email': ['Email', 'Email 1', 'Email Address', 'Contact Email', 'Enhanced_Email'],
            
            # Phone columns (perfect processor pattern) 
            'phone': ['Phone', 'Phone 1', 'Contact Phone', 'Phone Number', 'Contact Phone 1', 'Enhanced_Phone'],
            
            # Company columns (perfect processor pattern)
            'company': ['Company', 'Company Name', 'Organization', 'Company Name - Cleaned'],
            
            # Additional fields perfect processor handles
            'title': ['Title', 'Job Title', 'Position', 'Role'],
            'first_name': ['First Name', 'FirstName', 'first_name'],
            'last_name': ['Last Name', 'LastName', 'last_name'],
            'revenue': ['Company Annual Revenue', 'Annual Revenue', 'Revenue'],
            'linkedin': ['Contact LI Profile URL', 'LinkedIn', 'LinkedIn URL', 'LinkedIn Profile'],
            'location': ['Contact Location', 'Location', 'Address'],
            'description': ['Description', 'Business Mission Statement', 'Notes']
        }
    
    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names to match what perfect_processor.py expects.
        Always ensure a 'Contact Full Name' column exists, creating it from first/last name if needed.
        """
        df_copy = df.copy()
        column_renames = {}
        used_names = set()  # Track names we've already used

        for col in df_copy.columns:
            col_clean = str(col).strip()
            col_lower = col_clean.lower()

            # Skip if we've already processed this column
            if col in column_renames:
                continue

            # Check if this column matches any of our standard patterns
            renamed = False
            for field_type, standard_names in self.standard_columns.items():
                for standard_name in standard_names:
                    # Skip if we've already used this standard name
                    if standard_name in used_names:
                        continue

                    if col_lower == standard_name.lower():
                        # Already in standard format
                        if col_clean != standard_name:
                            column_renames[col] = standard_name
                            used_names.add(standard_name)
                        renamed = True
                        break
                    # Partial matches for key fields
                    elif field_type == 'name' and 'full name' in col_lower and not renamed:
                        if 'Contact Full Name' not in used_names:
                            column_renames[col] = 'Contact Full Name'
                            used_names.add('Contact Full Name')
                            renamed = True
                    elif field_type == 'email' and 'email' in col_lower and '1' in col_lower and not renamed:
                        if 'Email 1' not in used_names:
                            column_renames[col] = 'Email 1'
                            used_names.add('Email 1')
                            renamed = True
                    elif field_type == 'phone' and 'phone' in col_lower and '1' in col_lower and not renamed:
                        # Handle Contact Phone 1 vs Company Phone 1
                        if 'contact' in col_lower and 'Contact Phone 1' not in used_names:
                            column_renames[col] = 'Contact Phone 1'
                            used_names.add('Contact Phone 1')
                            renamed = True
                        elif 'company' in col_lower and 'Company Phone 1' not in used_names:
                            # Keep Company Phone 1 as is (different field)
                            renamed = True
                    elif field_type == 'company' and 'company' in col_lower and 'clean' in col_lower and not renamed:
                        if 'Company Name - Cleaned' not in used_names:
                            column_renames[col] = 'Company Name - Cleaned'
                            used_names.add('Company Name - Cleaned')
                            renamed = True
                if renamed:
                    break

        # Apply renames
        if column_renames:
            df_copy = df_copy.rename(columns=column_renames)
            logger.info(f"📝 Standardized columns: {column_renames}")

        # --- Ensure 'Contact Full Name' exists only if missing (original logic) ---
        name_cols = [c for c in df_copy.columns if str(c).strip().lower() in ['contact full name', 'full name', 'name']]
        if not name_cols:
            # Try to create from first/last name
            first_name_col = None
            last_name_col = None
            for c in df_copy.columns:
                c_lower = str(c).strip().lower()
                if c_lower in ['first name', 'firstname', 'first_name']:
                    first_name_col = c
                if c_lower in ['last name', 'lastname', 'last_name']:
                    last_name_col = c
            if first_name_col and last_name_col:
                df_copy['Contact Full Name'] = (
                    df_copy[first_name_col].astype(str).fillna('') + ' ' + df_copy[last_name_col].astype(str).fillna('')
                ).str.strip()
                logger.info("🧩 Created 'Contact Full Name' from first and last name columns.")
            elif first_name_col:
                df_copy['Contact Full Name'] = df_copy[first_name_col].astype(str).fillna('').str.strip()
                logger.info("🧩 Created 'Contact Full Name' from first name column only.")
            elif last_name_col:
                df_copy['Contact Full Name'] = df_copy[last_name_col].astype(str).fillna('').str.strip()
                logger.info("🧩 Created 'Contact Full Name' from last name column only.")
            else:
                logger.warning("⚠️ No name columns found to create 'Contact Full Name'.")

        # --- Ensure 'Company' column exists for perfect_processor.py ---
        company_cols = [c for c in df_copy.columns if str(c).strip().lower() in ['company', 'company name', 'company name - cleaned', 'organization']]
        if 'Company' not in df_copy.columns:
            # Prefer 'Company Name - Cleaned', then 'Company Name', then 'Organization'
            preferred = None
            for cname in ['Company Name - Cleaned', 'Company Name', 'Organization']:
                if cname in df_copy.columns:
                    preferred = cname
                    break
            if preferred:
                df_copy['Company'] = df_copy[preferred]
                logger.info(f"🧩 Created 'Company' column from '{preferred}'.")
            else:
                logger.warning("⚠️ No company columns found to create 'Company'.")

        return df_copy
    
    def validate_contact_info(self, df: pd.DataFrame):
        """
        Validate and count contacts with email/phone (like perfect_processor does)
        """
        email_patterns = ['email', 'enhanced_email']
        phone_patterns = ['phone', 'enhanced_phone']
        
        for idx, row in df.iterrows():
            has_email = False
            has_phone = False
            # Check for emails
            for col in df.columns:
                col_lower = str(col).lower()
                if any(pattern in col_lower for pattern in email_patterns):
                    value = row[col]
                    if pd.notna(value) and str(value) != '' and '@' in str(value):
                        has_email = True
                        break
            # Check for phones
            for col in df.columns:
                col_lower = str(col).lower()
                if any(pattern in col_lower for pattern in phone_patterns):
                    value = row[col]
                    if pd.notna(value) and str(value) != '':
                        # Extract digits to validate phone
                        digits = re.sub(r'\D', '', str(value))
                        if len(digits) >= 10:
                            has_phone = True
                            break
            if has_email:
                self.stats['contacts_with_email'] += 1
            if has_phone:
                self.stats['contacts_with_phone'] += 1
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data while preserving everything perfect_processor needs
        """
        # Remove completely empty rows
        df = df.dropna(how='all', axis=0)
        
        # Remove completely empty columns
        df = df.dropna(how='all', axis=1)
        
        # Don't convert to string for revenue columns (keep numeric)
        revenue_cols = ['Company Annual Revenue', 'Annual Revenue', 'Revenue']
        
        for col in df.columns:
            if col not in revenue_cols:
                # Convert to string and clean
                df[col] = df[col].astype(str).replace('nan', '').replace('None', '')
                # Strip whitespace
                if df[col].dtype == 'object':
                    df[col] = df[col].str.strip()
        
        return df
    
    def enhance_with_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pre-enhance the CSV with pattern detection similar to perfect_processor
        This helps perfect_processor find even more leads
        """
        logger.info("🔍 Pre-enhancing with pattern detection...")
        
        # Email pattern for detection
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Phone pattern for detection (10+ digits)
        phone_pattern = r'[\d\s\(\)\-\+]{10,}'
        
        enhanced_emails = []
        enhanced_phones = []
        
        for idx, row in df.iterrows():
            row_emails = []
            row_phones = []
            
            # Scan all columns for patterns
            for col in df.columns:
                value = str(row[col]) if pd.notna(row[col]) else ''
                
                # Find emails
                email_matches = re.findall(email_pattern, value)
                row_emails.extend(email_matches)
                
                # Find phones
                if re.search(phone_pattern, value):
                    digits = re.sub(r'\D', '', value)
                    if len(digits) >= 10:
                        row_phones.append(value)
            
            # Add to enhanced columns if found
            enhanced_emails.append(row_emails[0] if row_emails else '')
            enhanced_phones.append(row_phones[0] if row_phones else '')
        
        # Add enhanced columns if we found new data
        if any(enhanced_emails):
            df['Enhanced_Email'] = enhanced_emails
            logger.info(f"✨ Added Enhanced_Email column with {sum(1 for e in enhanced_emails if e)} values")
        
        if any(enhanced_phones):
            df['Enhanced_Phone'] = enhanced_phones
            logger.info(f"✨ Added Enhanced_Phone column with {sum(1 for e in enhanced_phones if e)} values")
        
        return df
    
    def process_xlsx_file(self, file_path: Path) -> List[Tuple[str, pd.DataFrame]]:
        """
        Process a single XLSX file
        """
        results = []
        
        try:
            # Read Excel file
            logger.info(f"📖 Reading {file_path.name}...")
            
            # Try to read with different engines for compatibility
            try:
                xlsx_file = pd.ExcelFile(file_path, engine='openpyxl')
            except:
                xlsx_file = pd.ExcelFile(file_path, engine='xlrd')
            
            sheet_names = xlsx_file.sheet_names
            logger.info(f"📑 Found {len(sheet_names)} sheet(s): {sheet_names}")
            
            for sheet_name in sheet_names:
                logger.info(f"  📄 Processing sheet: '{sheet_name}'")
                
                # Read the sheet
                df = pd.read_excel(xlsx_file, sheet_name=sheet_name)
                
                # Skip empty sheets
                if df.empty or len(df) == 0:
                    logger.warning(f"    ⚠️ Sheet '{sheet_name}' is empty, skipping")
                    continue
                
                # Clean the data
                df = self.clean_data(df)
                
                if df.empty:
                    logger.warning(f"    ⚠️ Sheet '{sheet_name}' is empty after cleaning")
                    continue
                
                # Standardize columns for perfect_processor
                df = self.standardize_columns(df)
                
                # Pre-enhance with pattern detection
                df = self.enhance_with_patterns(df)
                
                # Validate contact info
                self.validate_contact_info(df)
                
                # Update stats
                self.stats['sheets_processed'] += 1
                self.stats['total_rows'] += len(df)
                self.stats['total_columns'] += len(df.columns)
                
                # Log info
                logger.info(f"    ✅ Processed {len(df)} rows, {len(df.columns)} columns")
                
                # Show first few column names
                cols_preview = list(df.columns)[:8]
                if len(df.columns) > 8:
                    cols_preview.append(f"... and {len(df.columns) - 8} more")
                logger.info(f"    📋 Columns: {cols_preview}")
                
                # Check for key columns perfect_processor expects (robust to non-string headers)
                has_name = any('name' in str(col).lower() for col in df.columns)
                has_email = any('email' in str(col).lower() for col in df.columns)
                has_phone = any('phone' in str(col).lower() for col in df.columns)
                has_company = any('company' in str(col).lower() for col in df.columns)
                logger.info(f"    🔍 Key fields: Name={has_name}, Email={has_email}, Phone={has_phone}, Company={has_company}")
                
                results.append((sheet_name, df))
                
        except Exception as e:
            logger.error(f"❌ Error processing {file_path}: {str(e)}")
            self.stats['errors'].append({
                'file': file_path.name,
                'error': str(e)
            })
        
        return results
    
    def save_to_csv(self, df: pd.DataFrame, output_path: Path):
        """
        Save DataFrame to CSV compatible with perfect_processor.py
        """
        # Save with specific settings
        df.to_csv(
            output_path,
            index=False,
            encoding='utf-8',
            na_rep='',  # Empty string for NaN
            float_format='%.2f'  # Format floats for revenue
        )
        logger.info(f"💾 Saved CSV: {output_path}")
    
    def convert_file(self, file_path: Path, merge_sheets: bool = False) -> bool:
        """
        Convert a single XLSX file to CSV
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 Converting: {file_path.name}")
        logger.info(f"{'='*60}")
        
        # Process the XLSX file
        sheet_data = self.process_xlsx_file(file_path)
        
        if not sheet_data:
            logger.warning(f"⚠️ No data found in {file_path.name}")
            return False
        
        # Prepare base filename
        base_name = file_path.stem
        
        if merge_sheets and len(sheet_data) > 1:
            # Merge all sheets
            logger.info("🔄 Merging multiple sheets...")
            all_dfs = []
            
            for sheet_name, df in sheet_data:
                # Add source sheet column
                df['_source_sheet'] = sheet_name
                all_dfs.append(df)
            
            # Concatenate all
            merged_df = pd.concat(all_dfs, ignore_index=True, sort=False)
            
            # Save merged
            output_path = self.output_dir / f"{base_name}_merged.csv"
            self.save_to_csv(merged_df, output_path)
            
            logger.info(f"📊 Merged {len(sheet_data)} sheets → {len(merged_df)} total rows")
            
        else:
            # Save each sheet separately
            for sheet_name, df in sheet_data:
                if len(sheet_data) == 1:
                    # Single sheet - use original name
                    output_path = self.output_dir / f"{base_name}.csv"
                else:
                    # Multiple sheets - append sheet name
                    clean_sheet = sheet_name.replace(' ', '_').replace('/', '_')
                    output_path = self.output_dir / f"{base_name}_{clean_sheet}.csv"
                
                self.save_to_csv(df, output_path)
        
        self.stats['files_processed'] += 1
        return True
    
    def convert_all(self, merge_sheets: bool = False):
        """
        Convert all XLSX files in input directory
        """
        # Find all Excel files
        xlsx_files = list(self.input_dir.glob("*.xlsx")) + list(self.input_dir.glob("*.xls"))
        
        if not xlsx_files:
            logger.warning(f"⚠️ No XLSX/XLS files found in {self.input_dir}")
            return
        
        logger.info(f"📁 Found {len(xlsx_files)} file(s) to convert")
        
        # Process each
        for file_path in xlsx_files:
            self.convert_file(file_path, merge_sheets=merge_sheets)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print conversion summary"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 CONVERSION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Files processed: {self.stats['files_processed']}")
        logger.info(f"📑 Sheets processed: {self.stats['sheets_processed']}")
        logger.info(f"📝 Total rows: {self.stats['total_rows']:,}")
        logger.info(f"📋 Total columns: {self.stats['total_columns']}")
        logger.info(f"📧 Rows with emails found: {self.stats['contacts_with_email']}")
        logger.info(f"📞 Rows with phones found: {self.stats['contacts_with_phone']}")
        
        if self.stats['errors']:
            logger.error(f"\n❌ Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.error(f"  - {error['file']}: {error['error']}")
        else:
            logger.info("\n✨ No errors - conversion successful!")
        
        # Save stats
        stats_file = self.output_dir / "conversion_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        logger.info(f"\n📈 Detailed stats saved to: {stats_file}")
        
        # Advice for perfect_processor
        logger.info(f"\n💡 Next step: Run perfect_processor.py on the converted CSVs:")
        logger.info(f"   python perfect_processor.py --list-id YOUR_LIST_ID --csv-file data/csv_raw/YOUR_FILE.csv --test-mode")


def main():
    """Main function with CLI"""
    parser = argparse.ArgumentParser(
        description="Convert XLSX to CSV for Banyan Labs Perfect Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all XLSX files
  python xlsx_to_csv_converter.py
  
  # Convert specific file
  python xlsx_to_csv_converter.py --file "Arizona Commercial Real Estate.xlsx"
  
  # Test mode (first file only)
  python xlsx_to_csv_converter.py --test
  
  # Merge multi-sheet files
  python xlsx_to_csv_converter.py --merge-sheets
        """
    )
    
    parser.add_argument(
        '--input-dir',
        default='data/xlsx_raw',
        help='Input directory with XLSX files (default: data/xlsx_raw)'
    )
    parser.add_argument(
        '--output-dir',
        default='data/csv_raw',
        help='Output directory for CSV files (default: data/csv_raw)'
    )
    parser.add_argument(
        '--file',
        help='Convert specific file only'
    )
    parser.add_argument(
        '--merge-sheets',
        action='store_true',
        help='Merge multiple sheets into one CSV'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - process first file only'
    )
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = XLSXToCSVConverter(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    logger.info("🚀 Banyan Labs XLSX to CSV Converter")
    logger.info("📋 Optimized for perfect_processor.py")
    logger.info(f"📁 Input: {converter.input_dir}")
    logger.info(f"📁 Output: {converter.output_dir}")
    
    # Process files
    if args.file:
        # Specific file
        file_path = Path(args.file)
        if not file_path.exists():
            # Try in input directory
            file_path = converter.input_dir / args.file
        if not file_path.exists():
            logger.error(f"❌ File not found: {args.file}")
            sys.exit(1)
        converter.convert_file(file_path, merge_sheets=args.merge_sheets)
    elif args.test:
        # Test mode
        xlsx_files = list(converter.input_dir.glob("*.xlsx")) + list(converter.input_dir.glob("*.xls"))
        if xlsx_files:
            logger.info(f"🧪 Test mode: Converting {xlsx_files[0].name}")
            converter.convert_file(xlsx_files[0], merge_sheets=args.merge_sheets)
        else:
            logger.warning("⚠️ No XLSX files found for testing")
    else:
        # Interactive prompt for file path
        print("No file specified. Please enter the full path to the XLSX file you want to convert:")
        user_file = input("File path: ").strip()
        file_path = Path(user_file)
        if not file_path.exists():
            # Try in input directory
            file_path = converter.input_dir / user_file
        if not file_path.exists():
            logger.error(f"❌ File not found: {user_file}")
            sys.exit(1)
        converter.convert_file(file_path, merge_sheets=args.merge_sheets)


if __name__ == "__main__":
    main()
