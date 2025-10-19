import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase

from hirethon_template.url_shortener.tasks import process_bulk_upload_task
from hirethon_template.url_shortener.models import BulkUploadTask, ShortURL
from .factories import (
    BulkUploadTaskFactory,
    OrganizationFactory,
    NamespaceFactory,
    UserFactory,
    ShortURLFactory,
)


class TestProcessBulkUploadTask(TestCase):
    """Test process_bulk_upload Celery task"""
    
    def setUp(self):
        """Set up test environment"""
        self.user = UserFactory()
        self.organization = OrganizationFactory(created_by=self.user)
        self.namespace = NamespaceFactory(organization=self.organization, created_by=self.user)
    
    def test_process_bulk_upload_success(self):
        """Test successful bulk upload processing"""
        # Create bulk upload task
        task = BulkUploadTaskFactory(
            organization=self.organization,
            namespace=self.namespace,
            created_by=self.user,
            status=BulkUploadTask.Status.PENDING,
            total_urls=0
        )
        
        # Mock openpyxl workbook
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.active = mock_worksheet
        mock_workbook.save = MagicMock()
        
        # Mock worksheet data
        mock_worksheet.max_row = 3  # Header + 2 data rows
        
        # Mock the first row (headers) - this is what the task uses to find columns
        mock_worksheet.__getitem__.return_value = [
            MagicMock(value='original_url'),
            MagicMock(value='custom_short_code')
        ]
        
        # Mock the data rows
        mock_worksheet.iter_rows.return_value = [
            ['https://example.com', 'test1'],       # Row 1
            ['https://google.com', 'test2']         # Row 2
        ]
        
        with patch('hirethon_template.url_shortener.tasks.openpyxl.load_workbook') as mock_load:
            mock_load.return_value = mock_workbook
            
            result = process_bulk_upload_task(task.id)
            
            # Check result
            assert result is not None
            assert result['task_id'] == task.id
            assert result['status'] == 'completed'
            assert result['processed'] == 2
            assert result['failed'] == 0
    
    def test_process_bulk_upload_with_errors(self):
        """Test bulk upload processing with some errors"""
        task = BulkUploadTaskFactory(
            organization=self.organization,
            namespace=self.namespace,
            created_by=self.user,
            status=BulkUploadTask.Status.PENDING
        )
        
        # Mock openpyxl workbook with invalid data
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.active = mock_worksheet
        mock_workbook.save = MagicMock()
        
        # Mock worksheet data with errors
        mock_worksheet.max_row = 4  # Header + 3 data rows
        
        # Mock the first row (headers)
        mock_worksheet.__getitem__.return_value = [
            MagicMock(value='original_url'),
            MagicMock(value='custom_short_code')
        ]
        
        # Mock the data rows
        mock_worksheet.iter_rows.return_value = [
            ['https://example.com', 'test1'],       # Valid row
            ['', 'test2'],                          # Empty URL
            ['https://google.com', 'test3']         # Valid row
        ]
        
        with patch('hirethon_template.url_shortener.tasks.openpyxl.load_workbook') as mock_load:
            mock_load.return_value = mock_workbook
            
            result = process_bulk_upload_task(task.id)
            
            # Check result
            assert result is not None
            assert result['task_id'] == task.id
            assert result['status'] == 'completed'
            assert result['processed'] == 2  # 2 successful
            assert result['failed'] == 1     # 1 failed (empty URL)
    
    def test_process_bulk_upload_duplicate_short_codes(self):
        """Test bulk upload processing with duplicate short codes"""
        task = BulkUploadTaskFactory(
            organization=self.organization,
            namespace=self.namespace,
            created_by=self.user,
            status=BulkUploadTask.Status.PENDING
        )
        
        # Create existing short URL with same code
        ShortURLFactory(
            namespace=self.namespace,
            short_code='existing',
            created_by=self.user
        )
        
        # Mock openpyxl workbook with duplicate short code
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.active = mock_worksheet
        mock_workbook.save = MagicMock()
        
        # Mock worksheet data with duplicate
        mock_worksheet.max_row = 3  # Header + 2 data rows
        
        # Mock the first row (headers)
        mock_worksheet.__getitem__.return_value = [
            MagicMock(value='original_url'),
            MagicMock(value='custom_short_code')
        ]
        
        # Mock the data rows
        mock_worksheet.iter_rows.return_value = [
            ['https://example.com', 'existing'],     # Duplicate short code
            ['https://google.com', 'new']           # New short code
        ]
        
        with patch('hirethon_template.url_shortener.tasks.openpyxl.load_workbook') as mock_load:
            mock_load.return_value = mock_workbook
            
            result = process_bulk_upload_task(task.id)
            
            # Check result
            assert result is not None
            assert result['task_id'] == task.id
            assert result['status'] == 'completed'
            assert result['processed'] == 1  # 1 successful
            assert result['failed'] == 1    # 1 failed (duplicate)
    
    def test_process_bulk_upload_missing_required_columns(self):
        """Test bulk upload processing with missing required columns"""
        task = BulkUploadTaskFactory(
            organization=self.organization,
            namespace=self.namespace,
            created_by=self.user,
            status=BulkUploadTask.Status.PENDING
        )
        
        # Mock openpyxl workbook with missing required column
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.active = mock_worksheet
        mock_workbook.save = MagicMock()
        
        # Mock worksheet data with missing original_url column
        mock_worksheet.max_row = 2  # Header + 1 data row
        mock_worksheet.iter_rows.return_value = [
            ['wrong_column', 'custom_short_code'],  # Missing original_url
            ['https://example.com', 'test1']
        ]
        
        with patch('hirethon_template.url_shortener.tasks.openpyxl.load_workbook') as mock_load:
            mock_load.return_value = mock_workbook
            
            result = process_bulk_upload_task(task.id)
            
            # Check that task was marked as failed
            task.refresh_from_db()
            assert task.status == BulkUploadTask.Status.FAILED
            assert 'Required column \'original_url\' not found' in task.error_log
    
    def test_process_bulk_upload_empty_file(self):
        """Test bulk upload processing with empty file"""
        task = BulkUploadTaskFactory(
            organization=self.organization,
            namespace=self.namespace,
            created_by=self.user,
            status=BulkUploadTask.Status.PENDING
        )
        
        # Mock empty Excel file
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_workbook.active = mock_worksheet
        mock_workbook.save = MagicMock()
        
        # Mock empty worksheet (only header)
        mock_worksheet.max_row = 1  # Only header
        
        # Mock the first row (headers)
        mock_worksheet.__getitem__.return_value = [
            MagicMock(value='original_url'),
            MagicMock(value='custom_short_code')
        ]
        
        # Mock empty data rows
        mock_worksheet.iter_rows.return_value = []
        
        with patch('hirethon_template.url_shortener.tasks.openpyxl.load_workbook') as mock_load:
            mock_load.return_value = mock_workbook
            
            result = process_bulk_upload_task(task.id)
            
            # Check result
            assert result is not None
            assert result['task_id'] == task.id
            assert result['status'] == 'completed'
            assert result['processed'] == 0
            assert result['failed'] == 0
    
    def test_process_bulk_upload_task_not_found(self):
        """Test bulk upload processing when task is not found"""
        result = process_bulk_upload_task(99999)  # Non-existent task ID
        
        # Check result
        assert 'error' in result
        assert 'Task 99999 not found' in result['error']
    
    def test_process_bulk_upload_file_not_found(self):
        """Test bulk upload processing when file is not found"""
        task = BulkUploadTaskFactory(
            organization=self.organization,
            namespace=self.namespace,
            created_by=self.user,
            status=BulkUploadTask.Status.PENDING
        )
        
        # Mock file not found
        with patch('hirethon_template.url_shortener.tasks.openpyxl.load_workbook') as mock_load:
            mock_load.side_effect = FileNotFoundError("File not found")
            
            with pytest.raises(FileNotFoundError):
                process_bulk_upload_task(task.id)
    
    def test_process_bulk_upload_invalid_excel_format(self):
        """Test bulk upload processing with invalid Excel format"""
        task = BulkUploadTaskFactory(
            organization=self.organization,
            namespace=self.namespace,
            created_by=self.user,
            status=BulkUploadTask.Status.PENDING
        )
        
        # Mock invalid Excel format
        with patch('hirethon_template.url_shortener.tasks.openpyxl.load_workbook') as mock_load:
            mock_load.side_effect = Exception("Invalid Excel format")
            
            with pytest.raises(Exception):
                process_bulk_upload_task(task.id)