"""
==============================================================================
SYNTHETIC FRAUD DATA GENERATOR
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Generate realistic synthetic fraud data for testing and training models.
Supports various fraud patterns and scenarios.

PATTERNS SUPPORTED:
-------------------
- Card-not-present fraud
- Account takeover
- Synthetic identity
- First-party fraud
- Transaction velocity anomalies
- Geographic anomalies

USAGE:
------
    from app.data.fraud_generator import FraudDataGenerator
    
    generator = FraudDataGenerator(seed=42)
    data = generator.generate(n_samples=10000, fraud_ratio=0.05)
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from pathlib import Path

# Lazy imports
def _get_numpy():
    try:
        import numpy as np
        return np
    except ImportError:
        return None

def _get_pandas():
    try:
        import pandas as pd
        return pd
    except ImportError:
        return None


class FraudType(Enum):
    """Types of fraud scenarios."""
    CARD_NOT_PRESENT = "card_not_present"
    ACCOUNT_TAKEOVER = "account_takeover"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    FIRST_PARTY = "first_party"
    VELOCITY_ABUSE = "velocity_abuse"
    GEO_ANOMALY = "geo_anomaly"
    MERCHANT_COLLUSION = "merchant_collusion"


@dataclass
class Transaction:
    """Single transaction record."""
    transaction_id: str
    user_id: str
    amount: float
    merchant_id: str
    merchant_category: str
    timestamp: datetime
    card_present: bool
    channel: str
    device_type: str
    ip_address: str
    location_lat: float
    location_lng: float
    distance_from_home: float
    time_since_last_txn: float
    txn_count_1h: int
    txn_count_24h: int
    avg_txn_amount_30d: float
    is_fraud: bool
    fraud_type: Optional[str] = None
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


@dataclass
class UserProfile:
    """User profile for realistic generation."""
    user_id: str
    home_lat: float
    home_lng: float
    avg_amount: float
    std_amount: float
    typical_merchants: List[str]
    typical_hours: List[int]
    account_age_days: int
    device_ids: List[str]


class FraudDataGenerator:
    """
    Generate synthetic fraud data with realistic patterns.
    """
    
    # Merchant categories
    MERCHANT_CATEGORIES = [
        "grocery", "gas_station", "restaurant", "online_retail",
        "electronics", "clothing", "travel", "entertainment",
        "pharmacy", "utilities", "subscription", "atm"
    ]
    
    # Channels
    CHANNELS = ["pos", "online", "mobile", "phone", "atm"]
    
    # Device types
    DEVICE_TYPES = ["android", "ios", "desktop", "unknown"]
    
    def __init__(
        self,
        seed: int = 42,
        n_users: int = 1000,
        n_merchants: int = 500
    ):
        """
        Initialize generator.
        
        Args:
            seed: Random seed for reproducibility
            n_users: Number of unique users
            n_merchants: Number of unique merchants
        """
        self.seed = seed
        self.n_users = n_users
        self.n_merchants = n_merchants
        
        np = _get_numpy()
        if np is not None:
            np.random.seed(seed)
        random.seed(seed)
        
        # Generate user profiles
        self.users = self._generate_user_profiles()
        
        # Generate merchant IDs
        self.merchants = self._generate_merchants()
        
        # Transaction history for velocity features
        self._user_history: Dict[str, List[Transaction]] = {}
    
    def _generate_user_profiles(self) -> Dict[str, UserProfile]:
        """Generate user profiles with realistic attributes."""
        np = _get_numpy()
        users = {}
        
        for i in range(self.n_users):
            user_id = f"user_{i:06d}"
            
            # Random home location (US-centric)
            home_lat = random.uniform(25, 48)
            home_lng = random.uniform(-125, -70)
            
            # Spending patterns
            if np is not None:
                avg_amount = np.random.lognormal(4.5, 1.0)  # ~$90 average
                std_amount = avg_amount * random.uniform(0.3, 0.8)
            else:
                avg_amount = random.uniform(20, 500)
                std_amount = avg_amount * random.uniform(0.3, 0.8)
            
            # Typical behaviors
            typical_merchants = random.sample(
                self.MERCHANT_CATEGORIES,
                k=random.randint(3, 8)
            )
            typical_hours = sorted(random.sample(range(24), k=random.randint(8, 16)))
            
            users[user_id] = UserProfile(
                user_id=user_id,
                home_lat=home_lat,
                home_lng=home_lng,
                avg_amount=avg_amount,
                std_amount=std_amount,
                typical_merchants=typical_merchants,
                typical_hours=typical_hours,
                account_age_days=random.randint(30, 3650),
                device_ids=[f"device_{random.randint(1000, 9999)}" for _ in range(random.randint(1, 3))]
            )
        
        return users
    
    def _generate_merchants(self) -> List[Tuple[str, str]]:
        """Generate merchant IDs with categories."""
        merchants = []
        for i in range(self.n_merchants):
            merchant_id = f"merchant_{i:05d}"
            category = random.choice(self.MERCHANT_CATEGORIES)
            merchants.append((merchant_id, category))
        return merchants
    
    def _generate_ip(self) -> str:
        """Generate random IP address."""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate approximate distance in km."""
        np = _get_numpy()
        if np is not None:
            lat_diff = abs(lat1 - lat2)
            lng_diff = abs(lng1 - lng2)
            return np.sqrt(lat_diff**2 + lng_diff**2) * 111  # Rough km conversion
        else:
            lat_diff = abs(lat1 - lat2)
            lng_diff = abs(lng1 - lng2)
            return (lat_diff**2 + lng_diff**2)**0.5 * 111
    
    def _get_velocity_features(self, user_id: str, timestamp: datetime) -> Tuple[float, int, int]:
        """Calculate velocity features for a user."""
        history = self._user_history.get(user_id, [])
        
        if not history:
            return 0.0, 0, 0
        
        # Time since last transaction
        last_txn = history[-1]
        time_since_last = (timestamp - last_txn.timestamp).total_seconds() / 60
        
        # Transactions in last hour
        one_hour_ago = timestamp - timedelta(hours=1)
        txn_count_1h = sum(1 for t in history if t.timestamp > one_hour_ago)
        
        # Transactions in last 24 hours
        one_day_ago = timestamp - timedelta(days=1)
        txn_count_24h = sum(1 for t in history if t.timestamp > one_day_ago)
        
        return time_since_last, txn_count_1h, txn_count_24h
    
    def generate_legitimate_transaction(
        self,
        user: UserProfile,
        timestamp: datetime
    ) -> Transaction:
        """Generate a legitimate transaction."""
        np = _get_numpy()
        
        # Select merchant
        merchant_id, merchant_category = random.choice(self.merchants)
        
        # Prefer typical merchants
        if random.random() < 0.7 and user.typical_merchants:
            for m_id, m_cat in self.merchants:
                if m_cat in user.typical_merchants:
                    merchant_id, merchant_category = m_id, m_cat
                    break
        
        # Generate amount
        if np is not None:
            amount = max(0.01, np.random.normal(user.avg_amount, user.std_amount))
        else:
            amount = max(0.01, random.gauss(user.avg_amount, user.std_amount))
        
        # Location near home
        location_lat = user.home_lat + random.uniform(-0.5, 0.5)
        location_lng = user.home_lng + random.uniform(-0.5, 0.5)
        distance = self._calculate_distance(user.home_lat, user.home_lng, location_lat, location_lng)
        
        # Velocity features
        time_since_last, txn_1h, txn_24h = self._get_velocity_features(user.user_id, timestamp)
        
        # Average amount
        history = self._user_history.get(user.user_id, [])
        if history:
            recent = [t for t in history if (timestamp - t.timestamp).days <= 30]
            avg_30d = sum(t.amount for t in recent) / len(recent) if recent else user.avg_amount
        else:
            avg_30d = user.avg_amount
        
        return Transaction(
            transaction_id=self._generate_transaction_id(),
            user_id=user.user_id,
            amount=round(amount, 2),
            merchant_id=merchant_id,
            merchant_category=merchant_category,
            timestamp=timestamp,
            card_present=random.random() < 0.6,
            channel=random.choice(self.CHANNELS),
            device_type=random.choice(self.DEVICE_TYPES),
            ip_address=self._generate_ip(),
            location_lat=location_lat,
            location_lng=location_lng,
            distance_from_home=round(distance, 2),
            time_since_last_txn=round(time_since_last, 2),
            txn_count_1h=txn_1h,
            txn_count_24h=txn_24h,
            avg_txn_amount_30d=round(avg_30d, 2),
            is_fraud=False,
            fraud_type=None
        )
    
    def generate_fraud_transaction(
        self,
        user: UserProfile,
        timestamp: datetime,
        fraud_type: FraudType
    ) -> Transaction:
        """Generate a fraudulent transaction."""
        np = _get_numpy()
        
        merchant_id, merchant_category = random.choice(self.merchants)
        
        # Base transaction
        txn = self.generate_legitimate_transaction(user, timestamp)
        txn.is_fraud = True
        txn.fraud_type = fraud_type.value
        
        # Apply fraud patterns
        if fraud_type == FraudType.CARD_NOT_PRESENT:
            txn.card_present = False
            txn.channel = "online"
            if np is not None:
                txn.amount = max(100, np.random.lognormal(5.5, 1.5))  # Higher amounts
            else:
                txn.amount = random.uniform(100, 5000)
            txn.device_type = "desktop"
        
        elif fraud_type == FraudType.ACCOUNT_TAKEOVER:
            # Different device and location
            txn.device_type = random.choice([d for d in self.DEVICE_TYPES if d not in user.device_ids])
            txn.location_lat = random.uniform(25, 48)
            txn.location_lng = random.uniform(-125, -70)
            txn.distance_from_home = self._calculate_distance(
                user.home_lat, user.home_lng,
                txn.location_lat, txn.location_lng
            )
            txn.ip_address = self._generate_ip()
        
        elif fraud_type == FraudType.VELOCITY_ABUSE:
            # Multiple rapid transactions
            txn.txn_count_1h = random.randint(10, 50)
            txn.time_since_last_txn = random.uniform(0.1, 5)
        
        elif fraud_type == FraudType.GEO_ANOMALY:
            # Very far from home
            txn.location_lat = user.home_lat + random.uniform(-20, 20)
            txn.location_lng = user.home_lng + random.uniform(-40, 40)
            txn.distance_from_home = self._calculate_distance(
                user.home_lat, user.home_lng,
                txn.location_lat, txn.location_lng
            )
        
        elif fraud_type == FraudType.FIRST_PARTY:
            # High amount, new merchant category
            if np is not None:
                txn.amount = max(500, np.random.lognormal(6.5, 1.0))
            else:
                txn.amount = random.uniform(500, 10000)
            unusual_categories = [c for c in self.MERCHANT_CATEGORIES if c not in user.typical_merchants]
            if unusual_categories:
                txn.merchant_category = random.choice(unusual_categories)
        
        elif fraud_type == FraudType.SYNTHETIC_IDENTITY:
            # New user pattern
            if np is not None:
                txn.amount = np.random.lognormal(5.0, 0.5)
            else:
                txn.amount = random.uniform(100, 1000)
            txn.txn_count_24h = random.randint(0, 3)
        
        elif fraud_type == FraudType.MERCHANT_COLLUSION:
            txn.card_present = False
            txn.channel = "pos"
            if np is not None:
                txn.amount = round(np.random.uniform(1, 99.99), 2)  # Just under $100
            else:
                txn.amount = round(random.uniform(1, 99.99), 2)
        
        txn.amount = round(txn.amount, 2)
        return txn
    
    def generate(
        self,
        n_samples: int = 10000,
        fraud_ratio: float = 0.05,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """
        Generate dataset with specified fraud ratio.
        
        Args:
            n_samples: Total number of transactions
            fraud_ratio: Proportion of fraudulent transactions
            start_date: Start date for transactions
            end_date: End date for transactions
            
        Returns:
            List of Transaction objects
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=90)
        if end_date is None:
            end_date = datetime.now()
        
        n_fraud = int(n_samples * fraud_ratio)
        n_legit = n_samples - n_fraud
        
        transactions = []
        fraud_types = list(FraudType)
        
        # Generate legitimate transactions
        for _ in range(n_legit):
            user = random.choice(list(self.users.values()))
            timestamp = start_date + timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )
            txn = self.generate_legitimate_transaction(user, timestamp)
            transactions.append(txn)
            
            # Update history
            if user.user_id not in self._user_history:
                self._user_history[user.user_id] = []
            self._user_history[user.user_id].append(txn)
        
        # Generate fraud transactions
        for _ in range(n_fraud):
            user = random.choice(list(self.users.values()))
            timestamp = start_date + timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )
            fraud_type = random.choice(fraud_types)
            txn = self.generate_fraud_transaction(user, timestamp, fraud_type)
            transactions.append(txn)
        
        # Sort by timestamp
        transactions.sort(key=lambda t: t.timestamp)
        
        return transactions
    
    def to_dataframe(self, transactions: List[Transaction]) -> Any:
        """Convert transactions to pandas DataFrame."""
        pd = _get_pandas()
        if pd is None:
            return [t.to_dict() for t in transactions]
        
        data = [t.to_dict() for t in transactions]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def save(
        self,
        transactions: List[Transaction],
        path: str,
        format: str = "csv"
    ) -> None:
        """
        Save transactions to file.
        
        Args:
            transactions: List of transactions
            path: Output file path
            format: Output format (csv, json, parquet)
        """
        pd = _get_pandas()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            data = [t.to_dict() for t in transactions]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif pd is not None:
            df = self.to_dataframe(transactions)
            if format == "csv":
                df.to_csv(path, index=False)
            elif format == "parquet":
                df.to_parquet(path, index=False)
        else:
            # Fallback to JSON
            data = [t.to_dict() for t in transactions]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
    
    def get_statistics(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Get statistics about generated data."""
        n_total = len(transactions)
        n_fraud = sum(1 for t in transactions if t.is_fraud)
        
        fraud_by_type: Dict[str, int] = {}
        for t in transactions:
            if t.is_fraud and t.fraud_type:
                fraud_by_type[t.fraud_type] = fraud_by_type.get(t.fraud_type, 0) + 1
        
        amounts = [t.amount for t in transactions]
        
        return {
            "total_transactions": n_total,
            "fraud_count": n_fraud,
            "legitimate_count": n_total - n_fraud,
            "fraud_ratio": n_fraud / n_total if n_total > 0 else 0,
            "fraud_by_type": fraud_by_type,
            "amount_stats": {
                "min": min(amounts),
                "max": max(amounts),
                "mean": sum(amounts) / len(amounts),
            },
            "unique_users": len(set(t.user_id for t in transactions)),
            "unique_merchants": len(set(t.merchant_id for t in transactions))
        }


# CLI interface
if __name__ == "__main__":
    print("Generating synthetic fraud data...")
    
    generator = FraudDataGenerator(seed=42, n_users=500, n_merchants=200)
    transactions = generator.generate(n_samples=10000, fraud_ratio=0.05)
    
    stats = generator.get_statistics(transactions)
    print("\n📊 Dataset Statistics:")
    print(f"   Total: {stats['total_transactions']:,}")
    print(f"   Fraud: {stats['fraud_count']:,} ({stats['fraud_ratio']:.2%})")
    print(f"   Legitimate: {stats['legitimate_count']:,}")
    print("\n🔴 Fraud by Type:")
    for fraud_type, count in stats['fraud_by_type'].items():
        print(f"   {fraud_type}: {count}")
    
    # Save sample
    generator.save(transactions[:100], "data/synthetic/fraud_sample.json", format="json")
    print("\n✅ Sample saved to data/synthetic/fraud_sample.json")
