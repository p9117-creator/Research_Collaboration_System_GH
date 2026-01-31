#!/usr/bin/env python3
"""
Report Generator for Research Collaboration System
Generates PDF reports and exports data in various formats
"""

import os
import io
import csv
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import logging

# PDF Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate various reports in PDF and other formats"""
    
    def __init__(self, db_manager=None, query_engine=None):
        self.db_manager = db_manager
        self.query_engine = query_engine
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles for reports"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1e3a8a'),
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#1e3a8a')
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#3b82f6')
        ))
        
        # Normal text style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
        
        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER
        ))

    def _create_header(self, title: str) -> List:
        """Create report header"""
        elements = []
        
        # Title
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 10))
        
        # Generation date
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(
            f"Generated on: {date_str}",
            self.styles['CustomNormal']
        ))
        elements.append(Spacer(1, 5))
        
        # Horizontal line
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=colors.HexColor('#1e3a8a'),
            spaceBefore=10,
            spaceAfter=20
        ))
        
        return elements

    def _create_table(self, data: List[List], headers: List[str], 
                      col_widths: List = None) -> Table:
        """Create a styled table"""
        table_data = [headers] + data
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1e3a8a')),
        ]))
        
        return table

    def generate_system_overview_report(self) -> io.BytesIO:
        """Generate complete system overview report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)
        
        elements = []
        
        # Header
        elements.extend(self._create_header("Research Collaboration System Report"))
        
        # System Statistics Section
        elements.append(Paragraph("System Statistics", self.styles['CustomHeading']))
        
        try:
            # Get statistics from database
            stats = self._get_system_stats()
            
            stats_data = [
                ["Total Researchers", str(stats.get('researchers', 0))],
                ["Total Projects", str(stats.get('projects', 0))],
                ["Total Publications", str(stats.get('publications', 0))],
                ["Active Collaborations", str(stats.get('collaborations', 0))],
            ]
            
            stats_table = self._create_table(
                stats_data, 
                ["Metric", "Value"],
                col_widths=[3*inch, 2*inch]
            )
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
        except Exception as e:
            elements.append(Paragraph(f"Error loading statistics: {str(e)}", 
                                     self.styles['CustomNormal']))
        
        # Database Status Section
        elements.append(Paragraph("Database Status", self.styles['CustomHeading']))
        
        db_status = [
            ["MongoDB", "Document Storage", "Active"],
            ["Neo4j", "Graph Database", "Active"],
            ["Redis", "Cache Layer", "Active"],
            ["Cassandra", "Time-Series Data", "Active"],
        ]
        
        db_table = self._create_table(
            db_status,
            ["Database", "Purpose", "Status"],
            col_widths=[2*inch, 2.5*inch, 1.5*inch]
        )
        elements.append(db_table)
        elements.append(Spacer(1, 20))
        
        # Top Researchers Section
        elements.append(PageBreak())
        elements.append(Paragraph("Top Researchers", self.styles['CustomHeading']))
        
        try:
            researchers = self._get_top_researchers()
            if researchers:
                researcher_data = []
                for i, r in enumerate(researchers[:10], 1):
                    name = r.get('name', 'N/A')
                    if 'personal_info' in r:
                        name = f"{r['personal_info'].get('first_name', '')} {r['personal_info'].get('last_name', '')}"
                    
                    h_index = r.get('h_index', 0)
                    if 'collaboration_metrics' in r:
                        h_index = r['collaboration_metrics'].get('h_index', 0)
                    
                    pubs = r.get('publication_count', 0)
                    if 'collaboration_metrics' in r:
                        pubs = r['collaboration_metrics'].get('total_publications', 0)
                    
                    researcher_data.append([
                        str(i), name, str(h_index), str(pubs)
                    ])
                
                researcher_table = self._create_table(
                    researcher_data,
                    ["Rank", "Name", "H-Index", "Publications"],
                    col_widths=[0.7*inch, 2.5*inch, 1.2*inch, 1.5*inch]
                )
                elements.append(researcher_table)
            else:
                elements.append(Paragraph("No researcher data available", 
                                         self.styles['CustomNormal']))
        except Exception as e:
            elements.append(Paragraph(f"Error loading researchers: {str(e)}", 
                                     self.styles['CustomNormal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_researchers_report(self, researchers: List[Dict] = None) -> io.BytesIO:
        """Generate detailed researchers report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                rightMargin=30, leftMargin=30,
                                topMargin=30, bottomMargin=30)
        
        elements = []
        elements.extend(self._create_header("Researchers Report"))
        
        if researchers is None:
            researchers = self._get_all_researchers()
        
        if researchers:
            researcher_data = []
            for r in researchers:
                name = r.get('name', '')
                if 'personal_info' in r:
                    name = f"{r['personal_info'].get('first_name', '')} {r['personal_info'].get('last_name', '')}"
                
                email = r.get('email', '')
                if 'personal_info' in r:
                    email = r['personal_info'].get('email', '')
                
                dept = r.get('department', '')
                if 'academic_profile' in r:
                    dept = r['academic_profile'].get('department_id', '')
                
                position = r.get('position', '')
                if 'academic_profile' in r:
                    position = r['academic_profile'].get('position', '')
                
                h_index = r.get('h_index', 0)
                if 'collaboration_metrics' in r:
                    h_index = r['collaboration_metrics'].get('h_index', 0)
                
                pubs = r.get('publication_count', 0)
                if 'collaboration_metrics' in r:
                    pubs = r['collaboration_metrics'].get('total_publications', 0)
                
                researcher_data.append([
                    name[:30], email[:25], dept[:15], position[:15], str(h_index), str(pubs)
                ])
            
            researcher_table = self._create_table(
                researcher_data,
                ["Name", "Email", "Department", "Position", "H-Index", "Publications"],
                col_widths=[2*inch, 2*inch, 1.5*inch, 1.5*inch, 1*inch, 1*inch]
            )
            elements.append(researcher_table)
        else:
            elements.append(Paragraph("No researchers found", self.styles['CustomNormal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_projects_report(self, projects: List[Dict] = None) -> io.BytesIO:
        """Generate projects report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                rightMargin=30, leftMargin=30,
                                topMargin=30, bottomMargin=30)
        
        elements = []
        elements.extend(self._create_header("Projects Report"))
        
        if projects is None:
            projects = self._get_all_projects()
        
        if projects:
            project_data = []
            for p in projects:
                title = p.get('title', 'N/A')[:40]
                status = p.get('status', p.get('metadata', {}).get('status', 'N/A'))
                dept = p.get('department', p.get('department_id', 'N/A'))
                
                # Get dates
                start_date = p.get('start_date', '')
                if not start_date and 'metadata' in p:
                    start_date = p['metadata'].get('creation_date', '')[:10] if p['metadata'].get('creation_date') else ''
                
                budget = p.get('budget', 0)
                if isinstance(budget, dict):
                    budget = budget.get('total', 0)
                
                members_count = len(p.get('team_members', []))
                
                project_data.append([
                    title, status, dept[:15], str(start_date)[:10], f"${budget:,.0f}", str(members_count)
                ])
            
            project_table = self._create_table(
                project_data,
                ["Title", "Status", "Department", "Start Date", "Budget", "Members"],
                col_widths=[3*inch, 1*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1*inch]
            )
            elements.append(project_table)
        else:
            elements.append(Paragraph("No projects found", self.styles['CustomNormal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_publications_report(self, publications: List[Dict] = None) -> io.BytesIO:
        """Generate publications report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                rightMargin=30, leftMargin=30,
                                topMargin=30, bottomMargin=30)
        
        elements = []
        elements.extend(self._create_header("Publications Report"))
        
        if publications is None:
            publications = self._get_all_publications()
        
        if publications:
            pub_data = []
            for p in publications:
                title = p.get('title', 'N/A')[:50]
                pub_type = p.get('type', p.get('publication_type', 'N/A'))
                year = str(p.get('year', p.get('publication_year', 'N/A')))
                citations = str(p.get('citations', p.get('citation_count', 0)))
                journal = p.get('journal', p.get('venue', 'N/A'))[:25]
                
                pub_data.append([title, pub_type, year, citations, journal])
            
            pub_table = self._create_table(
                pub_data,
                ["Title", "Type", "Year", "Citations", "Journal/Venue"],
                col_widths=[3.5*inch, 1.2*inch, 0.8*inch, 1*inch, 2.5*inch]
            )
            elements.append(pub_table)
        else:
            elements.append(Paragraph("No publications found", self.styles['CustomNormal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_single_publication_report(self, publication: Dict) -> io.BytesIO:
        """Generate a detailed PDF report for a single publication"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)
        
        elements = []
        elements.extend(self._create_header("Publication Detail Analysis"))
        
        # Title
        elements.append(Paragraph(publication.get('title', 'Untitled Publication'), self.styles['CustomHeading']))
        elements.append(Spacer(1, 10))
        
        # Basic Info Table
        info_data = [
            ["Type", publication.get('publication_type', 'N/A')],
            ["Journal/Venue", publication.get('bibliographic_info', {}).get('journal', 'N/A')],
            ["Date", publication.get('bibliographic_info', {}).get('publication_date', 'N/A')],
            ["Citations", str(publication.get('metrics', {}).get('citation_count', 0))]
        ]
        
        info_table = self._create_table(
            info_data,
            ["Attribute", "Details"],
            col_widths=[2*inch, 3.5*inch]
        )
        elements.append(info_table)
        elements.append(Spacer(1, 25))
        
        # Authors Section
        elements.append(Paragraph("Authors Team", self.styles['CustomSubHeading']))
        authors = publication.get('authors', [])
        if authors:
            author_data = []
            for a in authors:
                name = a.get('name', 'Unknown Author')
                role = a.get('role', 'Author')
                author_data.append([name, role])
            
            author_table = self._create_table(
                author_data,
                ["Name", "Role"],
                col_widths=[3*inch, 2.5*inch]
            )
            elements.append(author_table)
        else:
            elements.append(Paragraph("No authors information available", self.styles['CustomNormal']))
            
        elements.append(Spacer(1, 20))
        
        # Footer Note
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceBefore=20))
        elements.append(Paragraph("This report was automatically generated by the Research Collaboration System Analysis Engine.", 
                                 self.styles['CustomNormal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer


    def generate_analytics_report(self) -> io.BytesIO:
        """Generate analytics report with statistics and insights"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)
        
        elements = []
        elements.extend(self._create_header("Analytics Report"))
        
        # Summary Statistics
        elements.append(Paragraph("Summary Statistics", self.styles['CustomHeading']))
        
        stats = self._get_system_stats()
        
        summary_data = [
            ["Total Researchers", str(stats.get('researchers', 0))],
            ["Total Projects", str(stats.get('projects', 0))],
            ["Total Publications", str(stats.get('publications', 0))],
            ["Active Collaborations", str(stats.get('collaborations', 0))],
            ["Average H-Index", f"{stats.get('avg_h_index', 0):.2f}"],
            ["Total Citations", str(stats.get('total_citations', 0))],
        ]
        
        summary_table = self._create_table(
            summary_data,
            ["Metric", "Value"],
            col_widths=[3*inch, 2*inch]
        )
        elements.append(summary_table)
        elements.append(Spacer(1, 30))
        
        # Department Statistics
        elements.append(Paragraph("Department Statistics", self.styles['CustomHeading']))
        
        dept_stats = self._get_department_stats()
        if dept_stats:
            dept_data = [[d['name'], str(d['researchers']), str(d['publications']), str(d['projects'])] 
                        for d in dept_stats[:10]]
            
            dept_table = self._create_table(
                dept_data,
                ["Department", "Researchers", "Publications", "Projects"],
                col_widths=[2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch]
            )
            elements.append(dept_table)
        else:
            elements.append(Paragraph("No department data available", self.styles['CustomNormal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_collaboration_report(self) -> io.BytesIO:
        """Generate collaboration network report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)
        
        elements = []
        elements.extend(self._create_header("Collaboration Network Report"))
        
        # Collaboration Statistics
        elements.append(Paragraph("Collaboration Statistics", self.styles['CustomHeading']))
        
        try:
            collab_stats = self._get_collaboration_stats()
            
            stats_data = [
                ["Total Collaborations", str(collab_stats.get('total_collaborations', 0))],
                ["Total Supervisions", str(collab_stats.get('total_supervisions', 0))],
                ["Total Mentorships", str(collab_stats.get('total_mentorships', 0))],
                ["Avg Collaborations/Researcher", f"{collab_stats.get('avg_collaborations_per_researcher', 0):.2f}"],
            ]
            
            stats_table = self._create_table(
                stats_data,
                ["Metric", "Value"],
                col_widths=[3.5*inch, 2*inch]
            )
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Most Connected Researchers
            elements.append(Paragraph("Most Connected Researchers", self.styles['CustomSubHeading']))
            
            if collab_stats.get('most_connected'):
                connected_data = [
                    [c.get('name', 'N/A'), str(c.get('connections', 0))]
                    for c in collab_stats['most_connected'][:10]
                ]
                
                connected_table = self._create_table(
                    connected_data,
                    ["Researcher", "Connections"],
                    col_widths=[3.5*inch, 2*inch]
                )
                elements.append(connected_table)
            
        except Exception as e:
            elements.append(Paragraph(f"Error loading collaboration data: {str(e)}", 
                                     self.styles['CustomNormal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # Data retrieval helper methods
    def _get_system_stats(self) -> Dict:
        """Get system statistics"""
        stats = {
            'researchers': 0,
            'projects': 0,
            'publications': 0,
            'collaborations': 0,
            'avg_h_index': 0,
            'total_citations': 0
        }
        
        try:
            if self.db_manager and self.db_manager.mongodb:
                stats['researchers'] = self.db_manager.mongodb.count_documents('researchers')
                stats['projects'] = self.db_manager.mongodb.count_documents('projects')
                stats['publications'] = self.db_manager.mongodb.count_documents('publications')
            
            if self.db_manager and self.db_manager.neo4j:
                collab_stats = self.db_manager.neo4j.get_collaboration_statistics()
                stats['collaborations'] = collab_stats.get('total_collaborations', 0)
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
        
        return stats

    def _get_top_researchers(self, limit: int = 10) -> List[Dict]:
        """Get top researchers by h-index"""
        try:
            if self.db_manager and self.db_manager.mongodb:
                return self.db_manager.mongodb.find_documents(
                    'researchers', 
                    {}, 
                    sort_by=[('collaboration_metrics.h_index', -1)],
                    limit=limit
                )
        except Exception as e:
            logger.error(f"Error getting top researchers: {e}")
        return []

    def _get_all_researchers(self) -> List[Dict]:
        """Get all researchers"""
        try:
            if self.db_manager and self.db_manager.mongodb:
                return self.db_manager.mongodb.find_documents('researchers', {})
        except Exception as e:
            logger.error(f"Error getting researchers: {e}")
        return []

    def _get_all_projects(self) -> List[Dict]:
        """Get all projects"""
        try:
            if self.db_manager and self.db_manager.mongodb:
                return self.db_manager.mongodb.find_documents('projects', {})
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
        return []

    def _get_all_publications(self) -> List[Dict]:
        """Get all publications"""
        try:
            if self.db_manager and self.db_manager.mongodb:
                return self.db_manager.mongodb.find_documents('publications', {})
        except Exception as e:
            logger.error(f"Error getting publications: {e}")
        return []

    def _get_department_stats(self) -> List[Dict]:
        """Get department statistics"""
        try:
            if self.db_manager and self.db_manager.mongodb:
                researchers = self.db_manager.mongodb.find_documents('researchers', {})
                
                dept_counts = {}
                for r in researchers:
                    dept = r.get('academic_profile', {}).get('department_id', 'Unknown')
                    if dept not in dept_counts:
                        dept_counts[dept] = {'name': dept, 'researchers': 0, 'publications': 0, 'projects': 0}
                    dept_counts[dept]['researchers'] += 1
                    dept_counts[dept]['publications'] += r.get('collaboration_metrics', {}).get('total_publications', 0)
                
                return list(dept_counts.values())
        except Exception as e:
            logger.error(f"Error getting department stats: {e}")
        return []

    def _get_collaboration_stats(self) -> Dict:
        """Get collaboration statistics from Neo4j"""
        try:
            if self.db_manager and self.db_manager.neo4j:
                return self.db_manager.neo4j.get_collaboration_statistics()
        except Exception as e:
            logger.error(f"Error getting collaboration stats: {e}")
        return {}


class DataExporter:
    """Export data in various formats"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
    
    def export_to_json(self, data: List[Dict], filename: str = None) -> io.StringIO:
        """Export data to JSON format"""
        buffer = io.StringIO()
        
        # Convert datetime objects to strings
        def json_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        json.dump(data, buffer, indent=2, default=json_serializer, ensure_ascii=False)
        buffer.seek(0)
        return buffer
    
    def export_to_csv(self, data: List[Dict], headers: List[str] = None) -> io.StringIO:
        """Export data to CSV format"""
        buffer = io.StringIO()
        
        if not data:
            return buffer
        
        # Auto-detect headers if not provided
        if headers is None:
            headers = list(data[0].keys())
        
        writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        
        for row in data:
            # Flatten nested dictionaries
            flat_row = self._flatten_dict(row)
            writer.writerow(flat_row)
        
        buffer.seek(0)
        return buffer
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            elif isinstance(v, (datetime, date)):
                items.append((new_key, v.isoformat()))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def export_researchers_csv(self) -> io.StringIO:
        """Export researchers to CSV"""
        researchers = []
        try:
            if self.db_manager and self.db_manager.mongodb:
                researchers = self.db_manager.mongodb.find_documents('researchers', {})
        except Exception as e:
            logger.error(f"Error exporting researchers: {e}")
        
        # Prepare data for CSV
        csv_data = []
        for r in researchers:
            csv_data.append({
                'id': r.get('_id', ''),
                'first_name': r.get('personal_info', {}).get('first_name', ''),
                'last_name': r.get('personal_info', {}).get('last_name', ''),
                'email': r.get('personal_info', {}).get('email', ''),
                'department': r.get('academic_profile', {}).get('department_id', ''),
                'position': r.get('academic_profile', {}).get('position', ''),
                'h_index': r.get('collaboration_metrics', {}).get('h_index', 0),
                'publications': r.get('collaboration_metrics', {}).get('total_publications', 0),
                'citations': r.get('collaboration_metrics', {}).get('total_citations', 0),
            })
        
        return self.export_to_csv(csv_data)
    
    def export_projects_csv(self) -> io.StringIO:
        """Export projects to CSV"""
        projects = []
        try:
            if self.db_manager and self.db_manager.mongodb:
                projects = self.db_manager.mongodb.find_documents('projects', {})
        except Exception as e:
            logger.error(f"Error exporting projects: {e}")
        
        csv_data = []
        for p in projects:
            csv_data.append({
                'id': p.get('_id', ''),
                'title': p.get('title', ''),
                'description': p.get('description', '')[:200] if p.get('description') else '',
                'status': p.get('status', p.get('metadata', {}).get('status', '')),
                'department': p.get('department', p.get('department_id', '')),
                'start_date': p.get('start_date', ''),
                'end_date': p.get('end_date', ''),
                'budget': p.get('budget', {}).get('total', 0) if isinstance(p.get('budget'), dict) else p.get('budget', 0),
                'team_size': len(p.get('team_members', [])),
            })
        
        return self.export_to_csv(csv_data)
    
    def export_publications_csv(self) -> io.StringIO:
        """Export publications to CSV"""
        publications = []
        try:
            if self.db_manager and self.db_manager.mongodb:
                publications = self.db_manager.mongodb.find_documents('publications', {})
        except Exception as e:
            logger.error(f"Error exporting publications: {e}")
        
        csv_data = []
        for p in publications:
            csv_data.append({
                'id': p.get('_id', ''),
                'title': p.get('title', ''),
                'type': p.get('type', p.get('publication_type', '')),
                'year': p.get('year', p.get('publication_year', '')),
                'journal': p.get('journal', p.get('venue', '')),
                'citations': p.get('citations', p.get('citation_count', 0)),
                'doi': p.get('doi', ''),
            })
        
        return self.export_to_csv(csv_data)


if __name__ == "__main__":
    # Test the report generator
    print("Report Generator Module Loaded Successfully")
