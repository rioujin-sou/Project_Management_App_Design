import re
import logging
import traceback
from typing import Dict, List, Any, Tuple
import pandas as pd
import datetime as dt
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def serialize_for_json(obj):
    """Convert dates/datetimes to ISO format strings for JSON serialization."""
    if isinstance(obj, (dt.date, dt.datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    return obj

class ExcelParserError(Exception):
    """Custom exception for Excel parsing errors"""
    pass


class ExcelParser:
    """
    Parser for project Excel files.
    Extracts project metadata from filename and task data from EffortEstimation sheet.
    """
    
    # Required columns in the EffortEstimation sheet
    REQUIRED_COLUMNS = [
        'Site', 'Category', 'Product', 'WP', 'WP-ID', 'Unit', 'Effort',
        'Comment', 'Tuning Factor', 'Qty', 'Total', 'Role', 
        'Resource Category', 'Support Type', 'SPC', 'Resource Name',
        'Start Date', 'End Date'
    ]
    
    # Optional columns
    OPTIONAL_COLUMNS = ['Rate', 'Cost']
    
    # Filename pattern: SCD PP DU APJ_{opp_id}_{name}_EE_v{version}.xlsx
    FILENAME_PATTERN = r'SCD PP DU APJ_([^_]+)_(.+)_EE_v(\d+)\.xlsx'
    
    def __init__(self, file_path: str, file_name: str):
        """Initialize parser with file path and file name"""
        self.file_path = Path(file_path)
        # FIX: was self.file_name (AttributeError) - should reference the parameter
        self.filename = file_name
        self.errors: List[str] = []
        logger.info(f"ExcelParser initialized with file_path={file_path}, file_name={file_name}")
        
    def parse_filename(self) -> Tuple[str, str, str]:
        """
        Extract opp_id, name, and version from filename.
        
        Returns:
            Tuple of (opp_id, name, version)
            
        Raises:
            ExcelParserError: If filename doesn't match expected pattern
        """
        logger.info(f"Parsing filename: {self.filename}")
        match = re.match(self.FILENAME_PATTERN, self.filename)
        if not match:
            raise ExcelParserError(
                f"Filename must match pattern: SCD PP DU APJ_{{opp_id}}_{{name}}_EE_v{{version}}.xlsx\n"
                f"Got: {self.filename}"
            )
        
        opp_id, name, version = match.groups()
        logger.info(f"Parsed filename - opp_id={opp_id}, name={name}, version={version}")
        return opp_id, name, version
    
    def validate_columns(self, df: pd.DataFrame) -> bool:
        """
        Validate that all required columns exist in the dataframe.
        
        Returns:
            True if all required columns exist, False otherwise
        """
        logger.info(f"Validating columns. Found columns: {list(df.columns)}")
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_columns:
            self.errors.append(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
            logger.error(f"Missing columns: {missing_columns}")
            return False
        
        logger.info("All required columns present")
        return True
    
    def validate_row(self, row: pd.Series, row_num: int) -> Dict[str, Any] | None:
        """
        Validate a single row and convert to task data.
        
        Returns:
            Dict with task data if valid, None if invalid (errors added to self.errors)
        """
        row_errors = []
        
        # Skip rows where Site is NaN (summary rows)
        if pd.isna(row['Site']):
            return None
        
        # Validate required string fields
        string_fields = ['Site', 'Category', 'Product', 'WP', 'WP-ID', 'Unit', 
                        'Role', 'Resource Category', 'Support Type', 'SPC']
        for field in string_fields:
            if pd.isna(row[field]) or str(row[field]).strip() == '':
                row_errors.append(f"{field} is required")
        
        # Validate numeric fields
        if pd.isna(row['Effort']) or row['Effort'] < 0:
            row_errors.append("Effort must be a non-negative number")
        
        if pd.isna(row['Tuning Factor']) or row['Tuning Factor'] < 0:
            row_errors.append("Tuning Factor must be a non-negative number")
        
        if pd.isna(row['Qty']) or row['Qty'] < 0:
            row_errors.append("Qty must be a non-negative number")
        
        if pd.isna(row['Total']) or row['Total'] < 0:
            row_errors.append("Total must be a non-negative number")
        
        # Validate dates
        if pd.isna(row['Start Date']):
            row_errors.append("Start Date is required")
        
        if pd.isna(row['End Date']):
            row_errors.append("End Date is required")
        
        if not pd.isna(row['Start Date']) and not pd.isna(row['End Date']):
            start = pd.to_datetime(row['Start Date'])
            end = pd.to_datetime(row['End Date'])
            if start > end:
                row_errors.append("Start Date must be before or equal to End Date")
        
        # If there are errors, add them to the main error list
        if row_errors:
            self.errors.append(f"Row {row_num}: {'; '.join(row_errors)}")
            logger.warning(f"Row {row_num} validation errors: {row_errors}")
            return None
        
        # Convert row to task data
        task_data = {
            'site': str(row['Site']).strip(),
            'category': str(row['Category']).strip(),
            'product': str(row['Product']).strip(),
            'wp': str(row['WP']).strip(),
            'wp_id': str(row['WP-ID']).strip(),
            'unit': str(row['Unit']).strip(),
            'effort': float(row['Effort']),
            'comment': str(row['Comment']).strip() if not pd.isna(row['Comment']) else None,
            'tuning_factor': float(row['Tuning Factor']),
            'qty': int(row['Qty']),
            'total': float(row['Total']),
            'role': str(row['Role']).strip(),
            'resource_category': str(row['Resource Category']).strip(),
            'support_type': str(row['Support Type']).strip(),
            'spc': str(row['SPC']).strip(),
            'resource_name': str(row['Resource Name']).strip() if not pd.isna(row['Resource Name']) else '',
            'start_date': pd.to_datetime(row['Start Date']).date(),
            'end_date': pd.to_datetime(row['End Date']).date(),
        }
        
        # Add optional columns if present
        if 'Rate' in row.index and not pd.isna(row['Rate']):
            task_data['rate'] = float(row['Rate'])
        else:
            task_data['rate'] = None
        
        if 'Cost' in row.index and not pd.isna(row['Cost']):
            task_data['cost'] = float(row['Cost'])
        else:
            task_data['cost'] = None
        
        return task_data
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the Excel file and extract project and task data.
        
        Returns:
            Dict with 'project' and 'tasks' keys
            
        Raises:
            ExcelParserError: If parsing fails with validation errors
        """
        self.errors = []  # Reset errors
        logger.info(f"Starting parse of file: {self.file_path}")
        
        # Parse filename
        try:
            opp_id, name, version = self.parse_filename()
        except ExcelParserError as e:
            logger.error(f"Filename parsing failed: {e}")
            raise e
        
        # Read Excel file
        try:
            df = pd.read_excel(self.file_path, sheet_name='EffortEstimation')
            df = df.dropna(subset=['WP', 'WP-ID'])
            logger.info(f"Excel file read successfully. Shape: {df.shape}, Columns: {list(df.columns)}")
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}\n{traceback.format_exc()}")
            raise ExcelParserError(f"Failed to read Excel file: {str(e)}")
        
        # Validate columns
        if not self.validate_columns(df):
            raise ExcelParserError("\n".join(self.errors))
        
        # Parse and validate rows
        tasks = []
        skipped_count = 0
        for idx, row in df.iterrows():
            # Row numbers start from 2 (1 is header, idx is 0-based)
            row_num = idx + 2
            try:
                task_data = self.validate_row(row, row_num)
                if task_data is not None:
                    tasks.append(task_data)
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error(f"Error processing row {row_num}: {e}\n{traceback.format_exc()}")
                self.errors.append(f"Row {row_num}: Unexpected error - {str(e)}")
        
        logger.info(f"Row processing complete. Valid tasks: {len(tasks)}, Skipped/invalid rows: {skipped_count}, Errors: {len(self.errors)}")
        
        # If there are validation errors, raise exception
        if self.errors:
            error_message = "Validation errors found:\n" + "\n".join(self.errors)
            logger.error(f"Validation failed: {error_message}")
            raise ExcelParserError(error_message)
        
        if not tasks:
            logger.error("No valid tasks found in the Excel file")
            raise ExcelParserError("No valid tasks found in the Excel file")
        
        # Create baseline JSON (snapshot of all tasks)
        # Serialize all date objects to ISO format strings for JSON compatibility
        serialized_tasks = serialize_for_json(tasks)
        baseline = {
            'opp_id': opp_id,
            'name': name,
            'version': version,
            'imported_at': datetime.utcnow().isoformat(),
            'task_count': len(tasks),
            'tasks': serialized_tasks
        }
        
        logger.info(f"Parse complete. Project: opp_id={opp_id}, name={name}, version={version}, tasks={len(tasks)}")
        
        return {
            'project': {
                'opp_id': opp_id,
                'name': name,
                'version': version,
                'baseline_json': baseline
            },
            'tasks': tasks
        }


def parse_excel_file(file_path: str, file_name: str) -> Dict[str, Any]:
    """
    Convenience function to parse an Excel file.
    
    Args:
        file_path: Path to the Excel file
        file_name: Original filename of the uploaded file
        
    Returns:
        Dict with 'project' and 'tasks' keys
        
    Raises:
        ExcelParserError: If parsing fails
    """
    logger.info(f"parse_excel_file called with file_path={file_path}, file_name={file_name}")
    parser = ExcelParser(file_path, file_name)
    return parser.parse()
