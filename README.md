# CSV Lead Processor

**Production-ready CSV to ClickUp lead processing automation tool**

Processes multiple CSV formats, cleans data, removes duplicates, and imports leads directly into ClickUp with proper field mapping and validation.

## 🎯 What This Does

Automates the entire lead import pipeline:
- **Multi-format CSV processing** - Handles Arizona, CTO lists, Hubspot exports, and generic formats
- **Smart data cleaning** - Phone formatting, email validation, company name standardization  
- **Intelligent deduplication** - Removes duplicates by email and company+name combinations
- **ClickUp integration** - Direct import to your ClickUp CRM with custom field mapping
- **Batch processing** - Rate-limited API calls to prevent timeouts

## 📊 Proven Production Results

**Latest Import Success (August 2025):**
- ✅ **19 CSV files** successfully processed
- ✅ **19,532 total leads** imported to ClickUp
- ✅ **Average 1,028 leads per file**
- ✅ **Zero data loss** with comprehensive validation

### Recent Successful Imports:
- Hubspot exports: 4,995 leads
- CTO call lists: 3,140 leads  
- Banyan email campaigns: 3,149 leads
- CPO contact lists: 1,560 leads
- Dental industry: 1,035 leads
- Arizona businesses: 1,340+ leads across multiple sectors
- Social impact orgs: 680+ nonprofits

## 🚀 Quick Start

### Prerequisites
```bash
# Clone the repo
git clone git@github.com:SamPomeroy/csv-lead-processor.git
cd csv-lead-processor

# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Get your ClickUp API token**:
   - Go to ClickUp Settings > Apps > API
   - Generate a new token
   - Copy the token (starts with `pk_`)

2. **Create `.env` file** in project root:
```bash
CLICKUP_TOKEN=pk_your_actual_token_here
```

That's it! The processor automatically detects your ClickUp custom fields. You'll specify the list ID when running the command.

## 💻 Usage

### Basic CSV Processing
```bash
# Test mode first (recommended)
python perfect_processor.py --csv-file "your_file.csv" --list-id 901317000000 --test-mode

# Production run (remove --test-mode)
python perfect_processor.py --csv-file "your_file.csv" --list-id 901317000000
```

### Excel to CSV Conversion (Optional)
```bash
# If you have .xlsx files, convert them first
python xlsx_to_csv_converter.py --input "your_file.xlsx"
```

### Command Line Options
```bash
# Full command structure
python perfect_processor.py --csv-file "path/to/file.csv" --list-id <clickup_list_id> [--test-mode]

# Examples:
python perfect_processor.py --csv-file "hubspot_leads.csv" --list-id 901317000000 --test-mode
python perfect_processor.py --csv-file "data/cto_leads.csv" --list-id 901317000000
```

## 🧪 Testing Mode

**Always test with small batches first using the `--test-mode` flag:**

```bash
# Test with first 5 leads
python perfect_processor.py --csv-file "your_file.csv" --list-id 901317000000 --test-mode
```

**Production Mode**: Remove the `--test-mode` flag to process all leads in the file.

## 📁 Project Structure
```
csv-lead-processor/
├── README.md                   # This file
├── perfect_processor.py        # Main processing script
├── requirements.txt           # Python dependencies
├── xlsx_to_csv_converter.py  # Excel conversion utility
├── .env                      # ClickUp API token (create this)
└── your_csv_files.csv       # Place CSV files here
```

## 🔧 Supported CSV Formats

The processor automatically detects and handles multiple formats:

### Arizona Business Format
- Columns: `Contact Full Name`, `Company Name - Cleaned`, `Email 1`, `Contact Phone 1`
- Used for: Real estate, restaurants, tech companies, nonprofits

### CTO/Executive Format  
- Columns: `Contact Full Name`, `Title`, `Company Name - Cleaned`, `Email 1`, `Company Annual Revenue`
- Used for: Executive contact lists, decision-maker databases

### Hubspot Export Format
- Columns: `First Name`, `Last Name`, `Email`, `Phone Number`, `Associated Company (Primary)`
- Used for: CRM exports, marketing lists

### Generic CSV Format
- Auto-detects common variations of: `name`, `company`, `email`, `phone`, `title`
- Fallback for unknown structures

## 🛠 Data Processing Features

### Phone Number Formatting
- **Input**: `888.793.8193`, `(888) 793-8193`, `888-793-8193`
- **Output**: `+1 888 793 8193` (ClickUp compatible)
- **Handles**: US numbers (10-digit and 11-digit with leading 1)

### Email Cleaning
- Standard emails: `email@domain.com`
- AI confidence format: `97% email@domain.com` → `email@domain.com`
- RFC validation and malformed email filtering

### Company Name Standardization
- Removes common suffixes (LLC, Inc, Corp, etc.)
- Proper capitalization formatting
- Duplicate company detection

### Deal Value Estimation
- **Revenue-based**: 0.1% of company annual revenue
- **Capped**: Between $1,000 and $500,000  
- **Defaults**: $5,000 (general), $7,500 (CTO), $10,000 (Hubspot)

## 🔄 Processing Pipeline

1. **File Detection** - Scans directory for CSV files
2. **Format Recognition** - Identifies CSV structure and maps columns
3. **Data Extraction** - Converts to standardized lead schema
4. **Cleaning & Validation** - Formats phones, validates emails, standardizes names
5. **Deduplication** - Removes duplicates by email and company+name pairs
6. **ClickUp Upload** - Batch creates tasks with custom fields (5 leads per API call)
7. **Results Logging** - Detailed success/failure reporting

## 🔍 Troubleshooting

### Common Issues

**"No CSV files found"**
- Ensure CSV files are in the project root directory
- Check file extensions (.csv required)
- Verify file permissions

**"ClickUp API errors"**  
- Verify API token in `.env` file is correct
- Check that list ID is properly configured
- Test with small batch first (5 leads)
- Ensure your ClickUp list has the expected custom fields

**"Phone number validation errors"**
- Invalid phone numbers are automatically skipped
- Check logs for specific formatting issues
- US phone numbers only (international numbers skipped)

**"Email validation failures"**
- Malformed emails are automatically filtered out
- AI confidence emails are parsed automatically
- Check logs for validation details

### Performance Notes
- **Processing Speed**: ~1,000 leads per minute
- **Memory Usage**: Optimized for large datasets (50K+ leads)
- **API Rate Limiting**: 2-second delays between API calls
- **Batch Size**: 5 leads per ClickUp API request

## 🚀 Production Tips

1. **Always test first** - Use test mode with 5 leads before full import
2. **Check your ClickUp setup** - Verify your list ID and ensure custom fields exist
3. **Monitor API limits** - ClickUp has rate limits, processor handles this automatically
4. **Large datasets** - For 10K+ leads, consider running in smaller batches
5. **Backup your data** - Keep original CSV files as backup

## 📋 Dependencies

```
pandas>=1.5.0
requests>=2.28.0  
python-dotenv>=0.19.0
openpyxl>=3.1.0
```

## 🎯 Future Enhancements

- [ ] Additional CSV format support
- [ ] Real-time duplicate detection across imports
- [ ] Company enrichment via external APIs  
- [ ] Email validation service integration
- [ ] Parallel processing for massive datasets
- [ ] Integration with other CRM systems

---

**Built for Banyan Labs** | **Production-tested with 19K+ successful imports**

Need help? Check the logs for detailed error messages or reach out to the dev team.
