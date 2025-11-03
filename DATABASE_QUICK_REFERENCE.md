# Real Estate Database - Quick Reference Guide

## Collections Overview

### 9 Main Collections:
1. **users** - User accounts (buyers, listers, admins)
2. **properties** - Property details with price history
3. **listings** - Active/inactive property listings
4. **verification_documents** - Identity & property verification
5. **saved_listings** - User's bookmarked properties
6. **property_comparisons** - Side-by-side property comparison
7. **reviews** - Ratings for properties/listers
8. **messages** - Internal messaging system
9. **notifications** - Alerts and announcements
10. **audit_logs** - Activity tracking

---

## Quick API Reference

### Users
```bash
POST   /api/users                    # Create user
GET    /api/users/{firebase_uid}     # Get user
PUT    /api/users/{firebase_uid}     # Update user
GET    /api/users?role=buyer         # List users
```

### Properties
```bash
POST   /api/properties               # Create property
GET    /api/properties/{id}          # Get property
PUT    /api/properties/{id}          # Update (auto price history)
GET    /api/properties?city=Austin   # Search properties
DELETE /api/properties/{id}          # Delete property
```

### Listings
```bash
POST   /api/listings                 # Create listing
GET    /api/listings/{id}            # Get listing (view++)
PUT    /api/listings/{id}            # Update listing
GET    /api/listings?status=active   # List listings
```

### Verification
```bash
POST   /api/verification-documents   # Upload document
GET    /api/verification-documents?status=pending
PUT    /api/verification-documents/{id}/verify  # Admin verify
```

### Saved & Comparisons
```bash
POST   /api/saved-listings           # Save property
GET    /api/saved-listings?user_firebase_uid=xyz
DELETE /api/saved-listings/{id}

POST   /api/comparisons              # Create comparison
GET    /api/comparisons?user_firebase_uid=xyz
```

### Reviews
```bash
POST   /api/reviews                  # Post review
GET    /api/reviews?target_id=xyz    # Get reviews
DELETE /api/reviews/{id}
```

### Messages
```bash
POST   /api/messages                 # Send message
GET    /api/messages?user_firebase_uid=xyz&conversation_with=abc
PUT    /api/messages/{id}/read       # Mark read
```

### Notifications
```bash
POST   /api/notifications            # Create notification
GET    /api/notifications?user_firebase_uid=xyz
PUT    /api/notifications/{id}/read
```

### Audit Logs
```bash
POST   /api/audit-logs               # Log action
GET    /api/audit-logs?action=search_performed
```

### Admin
```bash
PUT    /api/admin/users/{uid}/suspend     # Suspend user
PUT    /api/admin/users/{uid}/ban         # Ban user
GET    /api/admin/analytics               # Platform stats
```

---

## User Roles
- **visitor**: Browse only
- **buyer**: Search, save, compare, message
- **renter**: Same as buyer
- **lister**: Create listings, manage properties
- **admin**: Verification, moderation, analytics

---

## Listing Status Flow
```
pending → verified (by admin) → active → hidden/expired
         ↓
      rejected
```

---

## Key Features

### 1. Automatic Price History
```javascript
// When you update property price, history is auto-added:
{
  "price": 350000,
  "changed_at": "2025-01-15T10:30:00Z",
  "reason": "Price updated"
}
```

### 2. View Count Tracking
```
GET /api/listings/{id}  // Automatically increments views_count
```

### 3. Verification Auto-Update
```
When identity_proof is verified:
  verification_documents.status = "verified"
  → users.verification_status = "verified"
```

### 4. Broadcast Notifications
```javascript
// Send to all users:
{
  "user_firebase_uid": null,  // null = broadcast
  "title": "Platform Update",
  "message": "New features available!"
}
```

---

## Search Examples

### Search Properties
```bash
# By city and price range
GET /api/properties?city=Austin&min_price=200000&max_price=500000

# By property type
GET /api/properties?property_type=residential&limit=50
```

### Get User's Activity
```bash
# Saved listings
GET /api/saved-listings?user_firebase_uid=xyz

# Comparisons
GET /api/comparisons?user_firebase_uid=xyz

# Reviews written
GET /api/reviews?reviewer_firebase_uid=xyz

# Activity logs
GET /api/audit-logs?user_firebase_uid=xyz
```

### Admin Queries
```bash
# Pending verifications
GET /api/verification-documents?status=pending

# Pending listings
GET /api/listings?status=pending

# All listers
GET /api/users?role=lister
```

---

## Sample Data Flow

### New Lister Onboarding
```
1. Firebase signup → firebase_uid
2. POST /api/users (role="lister")
3. POST /api/verification-documents (identity_proof)
4. Admin: PUT /api/verification-documents/{id}/verify
5. User verification_status → "verified"
```

### Create & Publish Listing
```
1. POST /api/properties → property_id
2. POST /api/listings (property_id, lister_uid) → status: "pending"
3. Admin: PUT /api/listings/{id} (status="verified")
4. Listing goes live
```

### Buyer Journey
```
1. GET /api/properties (search)
2. POST /api/audit-logs (action="search_performed")
3. GET /api/listings/{id} (view property)
4. POST /api/saved-listings (bookmark)
5. POST /api/comparisons (compare with others)
6. POST /api/messages (contact lister)
7. POST /api/reviews (after viewing)
```

---

## Testing Commands

```bash
# Get backend URL
BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2 | tr -d '"')

# Create test user
curl -X POST $BACKEND_URL/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_uid": "test-123",
    "email": "test@example.com",
    "name": "Test User",
    "role": "buyer"
  }'

# Create test property
curl -X POST $BACKEND_URL/api/properties \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "prop-001",
    "title": "Test Property",
    "description": "A test property",
    "property_type": "residential",
    "current_price": 300000,
    "location": {
      "street": "123 Test St",
      "city": "Austin",
      "state": "TX",
      "zip_code": "78701",
      "country": "USA"
    },
    "bedrooms": 3,
    "bathrooms": 2
  }'

# Get analytics
curl $BACKEND_URL/api/admin/analytics
```

---

## Common Queries

```javascript
// Find all verified listers
GET /api/users?role=lister
// Then filter where verification_status === "verified"

// Get lister's properties
GET /api/listings?lister_firebase_uid=xyz
// Then fetch each property by property_id

// Get property reviews
GET /api/reviews?target_type=property&target_id=prop-001

// Get lister reviews
GET /api/reviews?target_type=lister&target_id=firebase-uid

// Get unread messages
GET /api/messages?user_firebase_uid=xyz
// Then filter where status === "unread"

// Get user's recent searches
GET /api/audit-logs?user_firebase_uid=xyz&action=search_performed
```

---

## Database Indexes

All collections have optimized indexes:
- **Unique**: firebase_uid, property_id, listing_id, etc.
- **Search**: city, state, status, role
- **Compound**: (user + listing), (city + state), (target_type + target_id)

→ Indexes created automatically on server startup

---

## Environment Setup

```bash
# Backend .env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="real_estate_db"
CORS_ORIGINS="*"

# Restart backend
sudo supervisorctl restart backend

# Check logs
tail -f /var/log/supervisor/backend.*.log
```

---

## Need Help?

For detailed documentation, see: `/app/DATABASE_DOCUMENTATION.md`

Key sections:
- Collection schemas
- API endpoint details
- Sample usage flows
- Security considerations