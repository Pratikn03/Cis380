# 📊 Behavioral Intelligence Feature Definitions

**Author:** Pratik Niroula  
**Project:** SentinelForge - Universal Anomaly Intelligence System

---

## 🎯 Overview

Behavioral Intelligence analyzes user activity patterns to detect anomalies,
potential insider threats, and unusual behaviors that deviate from established baselines.

---

## 📋 Core Feature Categories

### 1️⃣ Time-Based Features

| Feature | Description | Range | Anomaly Indicator |
|---------|-------------|-------|-------------------|
| `login_hour` | Hour of login (0-23) | 0-23 | Outside 8am-6pm |
| `login_day_of_week` | Day of week (0-6) | 0-6 | Weekend activity |
| `session_duration_mins` | Session length in minutes | 0-480 | > 4 hours or < 1 min |
| `time_since_last_login_hrs` | Hours since previous login | 0-inf | > 168 (1 week) |
| `login_frequency_24h` | Logins in last 24 hours | 0-100 | > 10 unusual |
| `after_hours_flag` | Activity outside business hours | 0/1 | 1 is flag |

### 2️⃣ Access Pattern Features

| Feature | Description | Range | Anomaly Indicator |
|---------|-------------|-------|-------------------|
| `unique_systems_accessed` | Distinct systems in session | 0-100 | > 10 unusual |
| `sensitive_files_accessed` | Count of sensitive file access | 0-1000 | > 20 flag |
| `failed_access_attempts` | Failed auth attempts | 0-100 | > 5 flag |
| `privilege_escalation_attempts` | Sudo/admin attempts | 0-50 | > 3 flag |
| `new_system_access_flag` | First time accessing system | 0/1 | 1 is notable |
| `access_velocity` | Access events per minute | 0-100 | > 20 suspicious |

### 3️⃣ Data Movement Features

| Feature | Description | Range | Anomaly Indicator |
|---------|-------------|-------|-------------------|
| `files_downloaded` | Files downloaded in session | 0-1000 | > 50 flag |
| `files_uploaded` | Files uploaded in session | 0-500 | > 20 flag |
| `data_transferred_mb` | Total data moved in MB | 0-10000 | > 1000 flag |
| `email_attachments_sent` | Email attachments count | 0-100 | > 10 flag |
| `usb_activity_flag` | USB device usage | 0/1 | 1 notable |
| `cloud_upload_mb` | Data uploaded to cloud | 0-5000 | > 500 flag |

### 4️⃣ Communication Features

| Feature | Description | Range | Anomaly Indicator |
|---------|-------------|-------|-------------------|
| `emails_sent` | Emails sent in session | 0-200 | > 50 flag |
| `external_recipients` | External email recipients | 0-100 | > 20 flag |
| `new_contact_flag` | Email to new address | 0/1 | 1 notable |
| `instant_messages` | IM count in session | 0-500 | > 100 flag |
| `vpn_connections` | VPN connection attempts | 0-20 | > 5 flag |

### 5️⃣ Application Usage Features

| Feature | Description | Range | Anomaly Indicator |
|---------|-------------|-------|-------------------|
| `apps_launched` | Unique applications used | 0-50 | > 20 unusual |
| `browser_tabs` | Browser tabs opened | 0-100 | > 30 flag |
| `admin_tools_used` | Admin/dev tools count | 0-20 | > 5 flag |
| `terminal_commands` | Terminal command count | 0-500 | > 100 flag |
| `code_commits` | Git commits in session | 0-50 | Context dependent |

### 6️⃣ Network Features

| Feature | Description | Range | Anomaly Indicator |
|---------|-------------|-------|-------------------|
| `unique_ips_contacted` | Distinct IPs contacted | 0-1000 | > 100 flag |
| `external_connections` | Connections outside org | 0-500 | > 50 flag |
| `dns_queries` | DNS lookup count | 0-5000 | > 1000 flag |
| `http_requests` | HTTP request count | 0-10000 | > 2000 flag |
| `blocked_site_attempts` | Blocked site access | 0-50 | > 5 flag |

### 7️⃣ Derived/Composite Features

| Feature | Description | Calculation |
|---------|-------------|-------------|
| `risk_score` | Overall risk assessment | Weighted sum of flags |
| `deviation_from_baseline` | How different from normal | Euclidean distance |
| `anomaly_score` | LOF/Isolation Forest score | Model output |
| `velocity_change` | Rate of activity change | Current/Historical ratio |
| `peer_deviation` | Difference from peer group | Z-score vs peer mean |

---

## 🔍 Baseline Calculation

### User Baseline (Individual)
```python
baseline = {
    "avg_session_duration": mean(last_30_days),
    "typical_login_hours": mode(login_hours),
    "avg_files_accessed": mean(files_accessed),
    "typical_systems": set(accessed_systems),
}
```

### Peer Group Baseline
```python
peer_baseline = {
    "department_avg_activity": dept_mean,
    "role_typical_access": role_systems,
    "team_working_hours": team_hours,
}
```

### Deviation Score
```python
deviation = sqrt(sum([
    (current[f] - baseline[f])**2 * weight[f]
    for f in features
]))
```

---

## 📊 Risk Level Thresholds

| Risk Level | Score Range | Action |
|------------|-------------|--------|
| Critical | 0.9 - 1.0 | Immediate review |
| High | 0.7 - 0.9 | Alert + investigation |
| Medium | 0.4 - 0.7 | Enhanced monitoring |
| Low | 0.2 - 0.4 | Standard logging |
| Normal | 0.0 - 0.2 | No action |

---

## 🚨 Alert Triggers

### Immediate Alerts
1. **Data Exfiltration Pattern**: Large file downloads + external upload
2. **After Hours Access**: Sensitive system access outside working hours
3. **Privilege Abuse**: Multiple privilege escalation attempts
4. **Credential Sharing**: Login from multiple locations simultaneously

### Monitoring Triggers
1. **Unusual Volume**: 3x normal activity level
2. **New System Access**: First-time access to sensitive system
3. **Peer Deviation**: Activity 2+ std dev from peer group

---

## 📈 Model Training Data Schema

```python
{
    "user_id": str,
    "timestamp": datetime,
    "session_id": str,
    "features": {
        # All features from categories above
    },
    "label": int,  # 0=normal, 1=anomalous (for supervised)
    "label_type": str,  # "confirmed_threat", "policy_violation", etc.
}
```

---

## 🔧 Feature Engineering Pipeline

```python
def engineer_features(raw_logs: pd.DataFrame) -> pd.DataFrame:
    """Transform raw logs into behavioral features."""
    
    # Time features
    df['login_hour'] = df['timestamp'].dt.hour
    df['is_weekend'] = df['timestamp'].dt.dayofweek >= 5
    
    # Rolling aggregations
    df['files_7d'] = df.groupby('user_id')['files'].transform(
        lambda x: x.rolling('7D').sum()
    )
    
    # Peer comparison
    df['peer_deviation'] = df.groupby('department')['activity'].transform(
        lambda x: (x - x.mean()) / x.std()
    )
    
    return df
```

---

## 📁 Data Sources

| Source | Features Extracted | Update Frequency |
|--------|-------------------|------------------|
| Active Directory | Login times, systems | Real-time |
| DLP System | File access, transfers | Real-time |
| Email Gateway | Email metadata | Hourly |
| Proxy Logs | Web activity | Real-time |
| Endpoint Agent | App usage, USB | Real-time |
| VPN Logs | Connection data | Real-time |

---

## ✅ Implementation Status

| Feature Category | Status | Notes |
|-----------------|--------|-------|
| Time-Based | ✅ Implemented | In orchestrator |
| Access Pattern | ✅ Implemented | Basic version |
| Data Movement | ⚠️ Partial | Needs DLP integration |
| Communication | ❌ Not implemented | Requires email API |
| Application | ⚠️ Partial | Basic tracking |
| Network | ⚠️ Partial | Needs proxy logs |
| Derived | ✅ Implemented | LOF model active |

---

*Document Version: 2.0 | Last Updated: January 7, 2026*
