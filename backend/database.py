"""
Database models and operations for EPIC issues dashboard
"""
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Issue(Base):
    """Issue model for storing Jira issues"""
    __tablename__ = 'issues'

    issue_key = Column(String, primary_key=True)
    summary = Column(Text)
    description = Column(Text)
    status = Column(String)
    priority = Column(String)
    category = Column(String)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    assignee = Column(String)
    reporter = Column(String)
    last_fetched = Column(DateTime, default=datetime.utcnow)


class DashboardStats(Base):
    """Store pre-calculated dashboard statistics"""
    __tablename__ = 'dashboard_stats'

    id = Column(Integer, primary_key=True)
    stat_date = Column(DateTime, default=datetime.utcnow)
    total_issues = Column(Integer)
    completed_issues = Column(Integer)
    in_progress_issues = Column(Integer)
    backlog_issues = Column(Integer)
    stats_json = Column(Text)  # Store additional stats as JSON


class Database:
    """Database manager class"""

    def __init__(self, db_path='./issues.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def upsert_issue(self, issue_data, commit=True):
        """Insert or update an issue"""
        issue = self.session.query(Issue).filter_by(
            issue_key=issue_data['issue_key']
        ).first()

        if issue:
            # Update existing issue
            for key, value in issue_data.items():
                setattr(issue, key, value)
        else:
            # Create new issue
            issue = Issue(**issue_data)
            self.session.add(issue)

        issue.last_fetched = datetime.utcnow()

        if commit:
            self.session.commit()

        return issue

    def commit(self):
        """Commit pending changes"""
        self.session.commit()

    def get_all_issues(self):
        """Get all issues"""
        return self.session.query(Issue).all()

    def get_issues_by_category(self, category):
        """Get issues filtered by category"""
        return self.session.query(Issue).filter_by(category=category).all()

    def get_issues_by_status(self, status):
        """Get issues filtered by status"""
        return self.session.query(Issue).filter_by(status=status).all()

    def get_category_stats(self):
        """Get statistics grouped by category"""
        from sqlalchemy import func

        results = self.session.query(
            Issue.category,
            func.count(Issue.issue_key).label('count')
        ).group_by(Issue.category).order_by(func.count(Issue.issue_key).desc()).all()

        return [{'name': r.category, 'value': r.count} for r in results]

    def get_status_stats(self):
        """Get statistics grouped by status"""
        from sqlalchemy import func

        results = self.session.query(
            Issue.status,
            func.count(Issue.issue_key).label('count')
        ).group_by(Issue.status).order_by(func.count(Issue.issue_key).desc()).all()

        return [{'name': r.status, 'value': r.count} for r in results]

    def get_priority_stats(self):
        """Get statistics grouped by priority"""
        from sqlalchemy import func

        results = self.session.query(
            Issue.priority,
            func.count(Issue.issue_key).label('count')
        ).group_by(Issue.priority).all()

        return [{'name': r.priority, 'value': r.count} for r in results]

    def get_category_details(self):
        """Get detailed breakdown by category and status"""
        from sqlalchemy import func

        results = self.session.query(
            Issue.category,
            Issue.status,
            func.count(Issue.issue_key).label('count')
        ).group_by(Issue.category, Issue.status).all()

        # Organize data by category
        category_details = {}
        for r in results:
            if r.category not in category_details:
                category_details[r.category] = {
                    'done': 0,
                    'inProgress': 0,
                    'backlog': 0,
                    'other': 0,
                    'total': 0
                }

            if r.status == 'Done':
                category_details[r.category]['done'] = r.count
            elif r.status == 'In Progress':
                category_details[r.category]['inProgress'] = r.count
            elif r.status == 'Backlog':
                category_details[r.category]['backlog'] = r.count
            else:
                category_details[r.category]['other'] += r.count

            category_details[r.category]['total'] += r.count

        # Calculate completion rates
        for category in category_details:
            total = category_details[category]['total']
            done = category_details[category]['done']
            if total > 0:
                category_details[category]['completion'] = round((done / total) * 100, 1)
            else:
                category_details[category]['completion'] = 0

        return category_details

    def close(self):
        """Close database session"""
        self.session.close()
