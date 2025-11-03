# Real Estate Listing Database Documentation

## Overview
This MongoDB database is designed for a comprehensive Real Estate Listing Website with Firebase authentication integration. The database consists of 9 main collections optimized for performance with proper indexing.

---

## Database Architecture

### Database Name: `real_estate_db`

### Collections Summary:
1. **users** - User accounts and profiles
2. **properties** - Property information with price history
3. **listings** - Active/inactive property listings
4. **verification_documents** - User and property verification docs
5. **saved_listings** - User's saved properties
6. **property_comparisons** - Property comparison lists
7. **reviews** - Property and lister reviews
8. **messages** - Internal messaging system
9. **notifications** - System alerts and announcements
10. **audit_logs** - Activity tracking and security logs

---

## Collection Details

### 1. USERS Collection

**Purpose**: Stores all user data with Firebase authentication integration

**Fields**:
```javascript
{
  firebase_uid: String (UNIQUE),        // Firebase authentication ID
  email: String,                        // User email
  name: String,                         // Full name
  role: Enum,                          // "visitor", "buyer", "renter", "lister", "admin"
  phone: String (optional),             // Contact number
  profile_picture: String (optional),   // Profile image URL
  verification_status: Enum,            // "pending", "verified", "rejected", "not_submitted"
  two_factor_enabled: Boolean,          // 2FA status
  is_suspended: Boolean,                // Admin suspension flag
  is_banned: Boolean,                   // Admin ban flag
  created_at: DateTime,
  updated_at: DateTime
}
```

**Indexes**:
- `firebase_uid` (unique)
- `email`
- `role`

**User Roles Explained**:
- **visitor**: Unregistered/basic users (browse only)
- **buyer**: Registered users looking to buy
- **renter**: Registered users looking to rent
- **lister**: Property owners/agents who create listings
- **admin**: Platform administrators

**API Endpoints**:
- `POST /api/users` - Create new user
- `GET /api/users/{firebase_uid}` - Get user by ID
- `PUT /api/users/{firebase_uid}` - Update user
- `GET /api/users?role=buyer&limit=100` - Get users with filters

---

### 2. PROPERTIES Collection

**Purpose**: Stores detailed property information

**Fields**:
```javascript
{
  property_id: String (UNIQUE),
  title: String,
  description: String,
  property_type: Enum,                 // "residential", "commercial", "land", "rental"
  current_price: Float,
  price_history: [                     // EMBEDDED: Track price changes
    {
      price: Float,
      changed_at: DateTime,
      reason: String
    }
  ],
  location: {                          // EMBEDDED: Address details
    street: String,
    city: String,
    state: String,
    zip_code: String,
    country: String,
    latitude: Float (optional),        // For mapping
    longitude: Float (optional)
  },
  bedrooms: Int (optional),
  bathrooms: Float (optional),
  area_sqft: Float (optional),
  year_built: Int (optional),
  amenities: [String],                 // e.g., ["pool", "garage", "gym"]
  images: [String],                    // Image URLs
  documents: [String],                 // Document URLs (ownership proof, etc.)
  virtual_tour_url: String (optional), // 360° tour link
  created_at: DateTime,
  updated_at: DateTime
}
```

**Indexes**:
- `property_id` (unique)
- `property_type`
- `current_price`
- `location.city` + `location.state` (compound)

**API Endpoints**:
- `POST /api/properties` - Create property
- `GET /api/properties/{property_id}` - Get property details
- `PUT /api/properties/{property_id}` - Update property (auto-tracks price history)
- `GET /api/properties?property_type=residential&min_price=100000&max_price=500000&city=Austin&limit=100`
- `DELETE /api/properties/{property_id}` - Delete property

**Price History Feature**: When you update `current_price`, a new entry is automatically added to `price_history` array.

---

### 3. LISTINGS Collection

**Purpose**: Links properties to listers and manages listing lifecycle

**Fields**:
```javascript
{
  listing_id: String (UNIQUE),
  property_id: String,                 // References properties collection
  lister_firebase_uid: String,         // References users collection
  status: Enum,                        // "active", "hidden", "pending", "verified", "rejected", "expired"
  views_count: Int,                    // Auto-incremented on view
  verified_at: DateTime (optional),
  verified_by_admin_uid: String (optional),
  rejection_reason: String (optional),
  expires_at: DateTime (optional),     // Listing expiration
  created_at: DateTime,
  updated_at: DateTime
}
```

**Indexes**:
- `listing_id` (unique)
- `property_id`
- `lister_firebase_uid`
- `status`

**Listing Status Workflow**:
1. **pending** → Newly created, awaiting admin approval
2. **verified** → Admin approved, visible to all
3. **active** → Live and searchable
4. **hidden** → Temporarily hidden by lister
5. **rejected** → Admin rejected
6. **expired** → Past expiration date

**API Endpoints**:
- `POST /api/listings` - Create listing
- `GET /api/listings/{listing_id}` - Get listing (increments view count)
- `PUT /api/listings/{listing_id}` - Update listing status
- `GET /api/listings?status=active&lister_firebase_uid=xyz&limit=100`

---

### 4. VERIFICATION_DOCUMENTS Collection

**Purpose**: Stores verification documents for users and properties

**Fields**:
```javascript
{
  document_id: String (UNIQUE),
  user_firebase_uid: String,
  document_type: String,               // "identity_proof", "property_ownership", "business_license"
  document_url: String,                // Storage URL
  status: Enum,                        // "pending", "verified", "rejected"
  verified_at: DateTime (optional),
  verified_by_admin_uid: String (optional),
  rejection_reason: String (optional),
  created_at: DateTime
}
```

**Indexes**:
- `document_id` (unique)
- `user_firebase_uid`
- `status`

**Document Types**:
- **identity_proof**: Government ID, passport (for all listers)
- **property_ownership**: Title deed, sale agreement
- **business_license**: For real estate agents

**API Endpoints**:
- `POST /api/verification-documents` - Upload document
- `GET /api/verification-documents/{document_id}`
- `GET /api/verification-documents?user_firebase_uid=xyz&status=pending`
- `PUT /api/verification-documents/{document_id}/verify` - Admin verification

**Special Feature**: When `identity_proof` is verified, user's `verification_status` is automatically updated to "verified".

---

### 5. SAVED_LISTINGS Collection

**Purpose**: Users can save properties for future reference

**Fields**:
```javascript
{
  saved_id: String (UNIQUE),
  user_firebase_uid: String,
  listing_id: String,
  notes: String (optional),            // Personal notes
  saved_at: DateTime
}
```

**Indexes**:
- `saved_id` (unique)
- `user_firebase_uid`
- `user_firebase_uid` + `listing_id` (compound, unique) - Prevents duplicate saves

**API Endpoints**:
- `POST /api/saved-listings` - Save a listing
- `GET /api/saved-listings?user_firebase_uid=xyz`
- `DELETE /api/saved-listings/{saved_id}` - Remove saved listing

---

### 6. PROPERTY_COMPARISONS Collection

**Purpose**: Users can compare multiple properties side-by-side

**Fields**:
```javascript
{
  comparison_id: String (UNIQUE),
  user_firebase_uid: String,
  property_ids: [String],              // Array of property IDs to compare
  created_at: DateTime
}
```

**Indexes**:
- `comparison_id` (unique)
- `user_firebase_uid`

**API Endpoints**:
- `POST /api/comparisons` - Create comparison
- `GET /api/comparisons?user_firebase_uid=xyz`
- `DELETE /api/comparisons/{comparison_id}`

---

### 7. REVIEWS Collection

**Purpose**: Users can review properties and listers

**Fields**:
```javascript
{
  review_id: String (UNIQUE),
  reviewer_firebase_uid: String,
  target_type: String,                 // "property" or "lister"
  target_id: String,                   // property_id or firebase_uid
  rating: Float,                       // 1-5 stars
  comment: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

**Indexes**:
- `review_id` (unique)
- `target_id`
- `target_type` + `target_id` (compound)

**API Endpoints**:
- `POST /api/reviews` - Create review
- `GET /api/reviews?target_type=property&target_id=xyz`
- `DELETE /api/reviews/{review_id}`

---

### 8. MESSAGES Collection

**Purpose**: Internal messaging between users (buyers ↔ listers)

**Fields**:
```javascript
{
  message_id: String (UNIQUE),
  sender_firebase_uid: String,
  receiver_firebase_uid: String,
  listing_id: String (optional),       // Context: which property
  subject: String (optional),
  content: String,
  status: Enum,                        // "unread", "read"
  sent_at: DateTime,
  read_at: DateTime (optional)
}
```

**Indexes**:
- `message_id` (unique)
- `sender_firebase_uid`
- `receiver_firebase_uid`
- `sent_at`

**API Endpoints**:
- `POST /api/messages` - Send message
- `GET /api/messages?user_firebase_uid=xyz` - Get all messages for user
- `GET /api/messages?user_firebase_uid=xyz&conversation_with=abc` - Get conversation
- `PUT /api/messages/{message_id}/read` - Mark as read

---

### 9. NOTIFICATIONS Collection

**Purpose**: System alerts and admin announcements

**Fields**:
```javascript
{
  notification_id: String (UNIQUE),
  user_firebase_uid: String (optional), // null = broadcast to all
  title: String,
  message: String,
  notification_type: String,            // "system", "listing_update", "message", "verification"
  is_read: Boolean,
  created_at: DateTime
}
```

**Indexes**:
- `notification_id` (unique)
- `user_firebase_uid`

**Notification Types**:
- **system**: Platform updates
- **listing_update**: Listing verified/rejected
- **message**: New message received
- **verification**: Document verification status

**API Endpoints**:
- `POST /api/notifications` - Create notification
- `GET /api/notifications?user_firebase_uid=xyz` - Get notifications (includes broadcasts)
- `PUT /api/notifications/{notification_id}/read` - Mark as read

---

### 10. AUDIT_LOGS Collection

**Purpose**: Track user activities for security and analytics

**Fields**:
```javascript
{
  log_id: String (UNIQUE),
  user_firebase_uid: String (optional),
  action: String,                      // "user_login", "property_viewed", "listing_created", "search_performed"
  resource_type: String (optional),    // "property", "user", "listing"
  resource_id: String (optional),
  metadata: Object,                    // Additional data: {search_filters, ip_address, etc.}
  timestamp: DateTime
}
```

**Indexes**:
- `log_id` (unique)
- `user_firebase_uid`
- `timestamp`
- `action`

**Common Actions**:
- `user_login`, `user_logout`
- `property_viewed`, `property_created`, `property_updated`
- `listing_created`, `listing_verified`
- `search_performed` (store filters in metadata)
- `document_uploaded`, `review_posted`

**API Endpoints**:
- `POST /api/audit-logs` - Create log
- `GET /api/audit-logs?user_firebase_uid=xyz&action=search_performed`

---

## Admin Endpoints

Special endpoints for admin operations:

```
PUT /api/admin/users/{firebase_uid}/suspend
PUT /api/admin/users/{firebase_uid}/ban
GET /api/admin/analytics
```

**Analytics Response**:
```javascript
{
  total_users: Int,
  total_properties: Int,
  total_listings: Int,
  active_listings: Int,
  pending_verifications: Int
}
```

---

## Key Features

### 1. Firebase Integration
- Uses `firebase_uid` instead of storing passwords
- Secure authentication handled by Firebase
- User data synced via `firebase_uid`

### 2. Automatic Price History
When you update a property's price:
```python
# Backend automatically adds to price_history array
{
  "price": 350000,
  "changed_at": "2025-01-15T10:30:00Z",
  "reason": "Price updated"
}
```

### 3. View Count Tracking
Every time someone views a listing, `views_count` increments automatically.

### 4. Verification Workflow
1. Lister uploads `identity_proof` → status: `pending`
2. Admin calls `/verify` endpoint → status: `verified`
3. User's `verification_status` automatically updates

### 5. Message Threading
Query conversations between two users:
```
GET /api/messages?user_firebase_uid=user1&conversation_with=user2
```

### 6. Broadcast Notifications
Set `user_firebase_uid: null` to send to all users.

---

## Database Indexes (Performance)

All critical fields have indexes for fast queries:
- **Unique indexes**: Prevent duplicates (e.g., `firebase_uid`, `property_id`)
- **Single indexes**: Fast lookups (e.g., `status`, `role`)
- **Compound indexes**: Multi-field queries (e.g., `city + state`, `user + listing`)

Indexes are automatically created on server startup.

---

## Data Relationships

```
USERS
  └─> LISTINGS (via lister_firebase_uid)
       └─> PROPERTIES (via property_id)
  └─> SAVED_LISTINGS (via user_firebase_uid)
  └─> PROPERTY_COMPARISONS (via user_firebase_uid)
  └─> REVIEWS (via reviewer_firebase_uid)
  └─> MESSAGES (via sender/receiver_firebase_uid)
  └─> NOTIFICATIONS (via user_firebase_uid)
  └─> AUDIT_LOGS (via user_firebase_uid)
  └─> VERIFICATION_DOCUMENTS (via user_firebase_uid)
```

---

## Sample Usage Flows

### Flow 1: User Registration (Buyer)
```
1. User signs up via Firebase → Get firebase_uid
2. POST /api/users (firebase_uid, email, name, role="buyer")
3. User profile created
```

### Flow 2: Lister Creates Property Listing
```
1. POST /api/properties (property details) → Get property_id
2. POST /api/listings (property_id, lister_firebase_uid) → status: "pending"
3. POST /api/verification-documents (identity_proof) → status: "pending"
4. Admin verifies document → User verification_status: "verified"
5. Admin updates listing status → "verified"
```

### Flow 3: Buyer Searches & Saves Property
```
1. GET /api/properties?city=Austin&min_price=200000&max_price=400000
2. POST /api/audit-logs (action="search_performed", metadata={filters})
3. GET /api/listings/{listing_id} → views_count++
4. POST /api/saved-listings (user_firebase_uid, listing_id)
```

### Flow 4: Buyer Contacts Lister
```
1. POST /api/messages (sender_uid, receiver_uid, listing_id, content)
2. POST /api/notifications (receiver_uid, type="message", title="New Message")
3. GET /api/messages?user_firebase_uid=receiver&conversation_with=sender
4. PUT /api/messages/{message_id}/read
```

### Flow 5: Admin Moderation
```
1. GET /api/verification-documents?status=pending
2. PUT /api/verification-documents/{doc_id}/verify (admin_uid, status="verified")
3. GET /api/listings?status=pending
4. PUT /api/listings/{listing_id} (status="verified")
5. GET /api/admin/analytics
```

---

## Security Considerations

1. **Firebase Authentication**: All API calls should verify Firebase tokens
2. **Role-Based Access**: Implement middleware to check user roles
3. **Data Privacy**: 
   - Buyers can't see lister contact info until they message
   - Admin-only endpoints require admin role verification
4. **Audit Logs**: Track all sensitive operations
5. **Password Storage**: No passwords stored (Firebase handles this)

---

## Environment Variables

```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="real_estate_db"
CORS_ORIGINS="*"
```

---

## Testing the Database

### Start the server:
```bash
sudo supervisorctl restart backend
```

### Test with curl:
```bash
# Get backend URL
BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2 | tr -d '"')

# Create a user
curl -X POST $BACKEND_URL/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_uid": "test-firebase-uid-123",
    "email": "john@example.com",
    "name": "John Doe",
    "role": "buyer",
    "phone": "+1234567890"
  }'

# Get user
curl $BACKEND_URL/api/users/test-firebase-uid-123

# Create a property
curl -X POST $BACKEND_URL/api/properties \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "prop-001",
    "title": "Beautiful 3BR House",
    "description": "Spacious family home",
    "property_type": "residential",
    "current_price": 350000,
    "location": {
      "street": "123 Main St",
      "city": "Austin",
      "state": "TX",
      "zip_code": "78701",
      "country": "USA"
    },
    "bedrooms": 3,
    "bathrooms": 2.5,
    "area_sqft": 2000,
    "amenities": ["pool", "garage"],
    "images": ["https://example.com/image1.jpg"]
  }'

# Search properties
curl "$BACKEND_URL/api/properties?city=Austin&min_price=300000&max_price=400000"

# Get analytics
curl $BACKEND_URL/api/admin/analytics
```

---

## Next Steps

1. **Add Firebase Authentication**: Implement Firebase token verification middleware
2. **Frontend Integration**: Connect React frontend to these APIs
3. **File Upload**: Implement image/document upload to Firebase Storage
4. **Search Enhancement**: Add full-text search with MongoDB Atlas Search
5. **Caching**: Implement Redis for frequently accessed data
6. **Rate Limiting**: Add API rate limiting for security

---

## Questions?

If you need clarification on:
- How to query specific data
- How relationships work
- How to implement authentication
- How to optimize queries

Feel free to ask!