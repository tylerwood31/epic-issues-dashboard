import React, { useState, useEffect } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import './Dashboard.css';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [allIssues, setAllIssues] = useState([]);
  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    const API_URL = process.env.REACT_APP_API_URL || '';
    try {
      const [dashboardResponse, issuesResponse, trendsResponse] = await Promise.all([
        axios.get(`${API_URL}/dashboard`),
        axios.get(`${API_URL}/issues`),
        axios.get(`${API_URL}/trends`)
      ]);

      if (dashboardResponse.data.success) {
        const data = dashboardResponse.data.data;

        // Add percentages to category data
        const total = data.total_issues;
        const categoryData = data.category_stats.map(cat => ({
          ...cat,
          percentage: total > 0 ? ((cat.value / total) * 100).toFixed(1) : 0
        }));

        setDashboardData({
          ...data,
          category_stats: categoryData
        });
        setLastUpdated(new Date(data.last_updated));
      }

      if (issuesResponse.data.success) {
        setAllIssues(issuesResponse.data.data);
      }

      if (trendsResponse.data.success) {
        setTrendsData(trendsResponse.data.data);
      }

      setLoading(false);
    } catch (err) {
      setError('Failed to fetch dashboard data. Make sure the backend is running.');
      setLoading(false);
    }
  };

  // Trigger manual refresh
  const handleRefresh = async () => {
    const API_URL = process.env.REACT_APP_API_URL || '';
    setRefreshing(true);
    try {
      await axios.post(`${API_URL}/refresh`);
      // Wait a few seconds then refresh the data
      setTimeout(() => {
        fetchDashboardData();
        setRefreshing(false);
      }, 3000);
    } catch (err) {
      setError('Failed to trigger refresh');
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Refresh data every 5 minutes
    const interval = setInterval(fetchDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={fetchDashboardData}>Retry</button>
      </div>
    );
  }

  if (!dashboardData) {
    return null;
  }

  const { total_issues, category_stats, status_stats, priority_stats, category_details } = dashboardData;

  // Calculate summary stats
  const completedIssues = status_stats.find(s => s.name === 'Done')?.value || 0;
  const inProgressIssues = status_stats.find(s => s.name === 'In Progress')?.value || 0;
  const backlogIssues = status_stats.find(s => s.name === 'Backlog')?.value || 0;
  const completionRate = total_issues > 0 ? ((completedIssues / total_issues) * 100).toFixed(0) : 0;

  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        {/* Header */}
        <div className="dashboard-header">
          <div className="header-content">
            <div>
              <h1>EPIC System Issues Dashboard</h1>
              <p className="subtitle">Comprehensive analysis of {total_issues} issues with automated categorization</p>
              {lastUpdated && (
                <p className="last-updated">Last updated: {lastUpdated.toLocaleString()}</p>
              )}
            </div>
            <button
              className={`refresh-button ${refreshing ? 'refreshing' : ''}`}
              onClick={handleRefresh}
              disabled={refreshing}
            >
              {refreshing ? 'Refreshing...' : '🔄 Refresh Data'}
            </button>
          </div>

          <div className="summary-cards">
            <div className="summary-card blue">
              <div className="card-value">{total_issues}</div>
              <div className="card-label">Total Issues</div>
            </div>
            <div className="summary-card green">
              <div className="card-value">{completedIssues}</div>
              <div className="card-label">Completed ({completionRate}%)</div>
            </div>
            <div className="summary-card orange">
              <div className="card-value">{inProgressIssues}</div>
              <div className="card-label">In Progress</div>
            </div>
            <div className="summary-card purple">
              <div className="card-value">{backlogIssues}</div>
              <div className="card-label">Backlog</div>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="charts-grid">
          {/* Category Distribution Pie Chart */}
          <div className="chart-card">
            <h2>Issues by Category</h2>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={category_stats}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  label={({ name, percentage }) => `${name}: ${percentage}%`}
                  outerRadius={90}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {category_stats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Status Distribution Bar Chart */}
          <div className="chart-card">
            <h2>Issues by Status</h2>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={status_stats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} interval={0} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#3b82f6" name="Number of Issues" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Volume Breakdown */}
        <div className="chart-card full-width">
          <h2>Category Volume Breakdown</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={category_stats} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={200} />
              <Tooltip />
              <Bar dataKey="value" fill="#10b981">
                {category_stats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Detailed Category Cards */}
        <div className="category-cards-grid">
          {Object.entries(category_details).map(([category, details], index) => (
            <div key={category} className="category-card">
              <div className="category-card-header">
                <h3>{category}</h3>
                <div className="category-count" style={{ color: COLORS[index % COLORS.length] }}>
                  {details.total}
                </div>
              </div>
              <div className="category-details">
                <div className="detail-row">
                  <span>Done:</span>
                  <span className="value green">{details.done}</span>
                </div>
                <div className="detail-row">
                  <span>In Progress:</span>
                  <span className="value blue">{details.inProgress}</span>
                </div>
                <div className="detail-row">
                  <span>Backlog:</span>
                  <span className="value orange">{details.backlog}</span>
                </div>
                <div className="detail-row">
                  <span>Other:</span>
                  <span className="value gray">{details.other}</span>
                </div>
                <div className="completion-section">
                  <div className="completion-header">
                    <span>Completion Rate:</span>
                    <span className="completion-rate">{details.completion}%</span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${details.completion}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Priority Distribution */}
        <div className="chart-card full-width">
          <h2>Priority Distribution</h2>
          <div className="priority-grid">
            {priority_stats.map((priority) => (
              <div key={priority.name} className="priority-card">
                <div className="priority-value">{priority.value}</div>
                <div className="priority-name">{priority.name}</div>
                <div className="priority-percentage">
                  {((priority.value / total_issues) * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly Trends */}
        {trendsData && trendsData.total && (
          <div className="chart-card full-width">
            <h2>Weekly Issue Trends</h2>
            <div className="trends-container">
              {/* Total Trend */}
              <div className="trend-section">
                <h3>Total Issues Created Per Week</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendsData.total}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="week" />
                    <YAxis />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="custom-tooltip">
                              <p><strong>Week: {data.week}</strong></p>
                              <p>Issues: {data.count}</p>
                              {data.change !== undefined && (
                                <p className={data.change >= 0 ? 'positive' : 'negative'}>
                                  Change: {data.change > 0 ? '+' : ''}{data.change}%
                                </p>
                              )}
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} name="Issues Created" dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Category Trends */}
              <div className="trend-section">
                <h3>Issues by Category (Weekly)</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={trendsData.total}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="week" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {Object.keys(trendsData.by_category).map((category, index) => (
                      <Line
                        key={category}
                        type="monotone"
                        dataKey="count"
                        data={trendsData.by_category[category]}
                        stroke={COLORS[index % COLORS.length]}
                        strokeWidth={2}
                        name={category}
                        dot={{ r: 3 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Category Trend Cards with % Change */}
              <div className="category-trends-grid">
                {Object.entries(trendsData.by_category).map(([category, data]) => {
                  const latestWeek = data[data.length - 1];
                  const previousWeek = data[data.length - 2];
                  return (
                    <div key={category} className="trend-card">
                      <h4>{category}</h4>
                      <div className="trend-value">{latestWeek.count}</div>
                      <div className="trend-label">This Week</div>
                      {latestWeek.change !== undefined && (
                        <div className={`trend-change ${latestWeek.change >= 0 ? 'positive' : 'negative'}`}>
                          {latestWeek.change > 0 ? '▲' : '▼'} {Math.abs(latestWeek.change)}%
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* All Issues Table */}
        <div className="chart-card full-width">
          <h2>All Issues ({allIssues.length})</h2>
          <div className="issues-table-container">
            <table className="issues-table">
              <thead>
                <tr>
                  <th>Issue Key</th>
                  <th>Summary</th>
                  <th>Status</th>
                  <th>Category</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                {allIssues.map((issue) => (
                  <tr key={issue.issue_key}>
                    <td className="issue-key">
                      <a
                        href={`https://coverwallet.atlassian.net/browse/${issue.issue_key}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {issue.issue_key}
                      </a>
                    </td>
                    <td className="issue-summary">{issue.summary}</td>
                    <td>
                      <span className={`status-badge status-${issue.status.toLowerCase().replace(/\s+/g, '-')}`}>
                        {issue.status}
                      </span>
                    </td>
                    <td className="issue-category">{issue.category}</td>
                    <td>
                      <span className={`priority-badge priority-${issue.priority.toLowerCase()}`}>
                        {issue.priority}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
