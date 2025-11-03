# Real Estate Database Schema - Visual Guide

## Database Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REAL ESTATE DATABASE                            │
│                         Database: real_estate_db                        │
└─────────────────────────────────────────────────────────────────────────┘


┌──────────────────────┐
│       USERS          │ (Main authentication & profile)
├──────────────────────┤
│ firebase_uid (PK)    │◄─────────────┐
│ email                │              │
│ name                 │              │
│ role                 │              │  References
│ verification_status  │              │
│ is_suspended         │              │
│ is_banned            │              │
└──────────────────────┘              │
         │                            │
         │ creates                    │
         ▼                            │
┌──────────────────────┐              │
│     PROPERTIES       │              │
├──────────────────────┤              │
│ property_id (PK)     │◄──┐          │
│ title                │   │          │
│ description          │   │          │
│ property_type        │   │          │
│ current_price        │   │          │
│ price_history[]      │   │ links to │
│ location{}           │   │          │
│ bedrooms             │   │          │
│ bathrooms            │   │          │
│ amenities[]          │   │          │
│ images[]             │   │          │
└──────────────────────┘   │          │
                           │          │
         │                 │          │
         │ has             │          │
         ▼                 │          │
┌──────────────────────┐   │          │
│      LISTINGS        │   │          │
├──────────────────────┤   │          │
│ listing_id (PK)      │   │          │
│ property_id (FK)─────┼───┘          │
│ lister_firebase_uid  │──────────────┘
│ status               │
│ views_count          │
│ verified_at          │
│ expires_at           │
└──────────────────────┘
         │
         │ referenced by
         │
    ┌────┴────┬──────────┬──────────────┐
    ▼         ▼          ▼              ▼
┌─────────┐ ┌────────┐ ┌─────────┐ ┌─────────┐
│  SAVED  │ │REVIEWS │ │MESSAGES │ │ AUDIT   │
│LISTINGS │ │        │ │         │ │  LOGS   │
└─────────┘ └────────┘ └─────────┘ └─────────┘
    │
    │ user saves
    │
┌──────────────────────┐
│ SAVED_LISTINGS       │
├──────────────────────┤
│ saved_id (PK)        │
│ user_firebase_uid    │─────┐
│ listing_id (FK)      │     │
│ notes                │     │
└──────────────────────┘     │
                             │
                             │ belongs to user
┌──────────────────────┐     │
│PROPERTY_COMPARISONS  │     │
├──────────────────────┤     │
│ comparison_id (PK)   │     │
│ user_firebase_uid    │◄────┤
│ property_ids[]       │     │
└──────────────────────┘     │
                             │
┌──────────────────────┐     │
│      REVIEWS         │     │
├──────────────────────┤     │
│ review_id (PK)       │     │
│ reviewer_uid         │◄────┤
│ target_type          │     │
│ target_id            │     │
│ rating (1-5)         │     │
│ comment              │     │
└──────────────────────┘     │
                             │
┌──────────────────────┐     │
│      MESSAGES        │     │
├──────────────────────┤     │
│ message_id (PK)      │     │
│ sender_uid           │◄────┤
│ receiver_uid         │◄────┘
│ listing_id           │
│ content              │
│ status (read/unread) │
└──────────────────────┘

┌──────────────────────┐
│   NOTIFICATIONS      │
├──────────────────────┤
│ notification_id (PK) │
│ user_firebase_uid    │ (null = broadcast)
│ title                │
│ message              │
│ is_read              │
└──────────────────────┘

┌──────────────────────┐
│VERIFICATION_DOCS     │
├──────────────────────┤
│ document_id (PK)     │
│ user_firebase_uid    │
│ document_type        │
│ document_url         │
│ status               │
│ verified_by_admin    │
└──────────────────────┘

┌──────────────────────┐
│    AUDIT_LOGS        │
├──────────────────────┤
│ log_id (PK)          │
│ user_firebase_uid    │
│ action               │
│ resource_type        │
│ resource_id          │
│ metadata{}           │
│ timestamp            │
└──────────────────────┘
```

---

## Data Flow Diagrams

### 1. New User Registration Flow
```
Firebase Auth
     │
     ▼
┌─────────────────┐
│ User signs up   │
│ Gets firebase_uid│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  POST /api/users│
│  (create profile)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   User created  │
│   in USERS      │
│   collection    │
└─────────────────┘
```

### 2. Property Listing Creation Flow
```
┌──────────────┐
│ LISTER       │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ POST /api/properties│ ─────┐
│ (create property)   │      │
└─────────┬───────────┘      │ Stores in
          │                  │ PROPERTIES
          │                  │
          ▼                  ▼
┌─────────────────────┐  ┌─────────┐
│ POST /api/listings  │  │property │
│ (create listing)    │  │price    │
└─────────┬───────────┘  │history[]│
          │              └─────────┘
          │ status: "pending"
          ▼
┌─────────────────────┐
│  POST /api/         │
│  verification-docs  │
│  (upload ID proof)  │
└─────────┬───────────┘
          │ status: "pending"
          ▼
┌─────────────────────┐
│   ADMIN reviews     │
│   and verifies      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ PUT /api/listings   │
│ status: "verified"  │
│ Listing goes LIVE!  │
└─────────────────────┘
```

### 3. Property Search & Save Flow
```
┌──────────────┐
│    BUYER     │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│ GET /api/properties     │
│ ?city=Austin            │
│ &min_price=300000       │
│ &max_price=500000       │
└─────────┬───────────────┘
          │
          ▼ Returns list
┌─────────────────────────┐
│ Buyer views properties  │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ GET /api/listings/{id}  │
│ (views_count++)         │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Buyer likes property    │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ POST /api/saved-listings│
│ (bookmark for later)    │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ POST /api/comparisons   │
│ (compare 2-3 properties)│
└─────────────────────────┘
```

### 4. Communication Flow
```
┌──────────┐                    ┌──────────┐
│  BUYER   │                    │  LISTER  │
└────┬─────┘                    └────┬─────┘
     │                               │
     │ Interested in property        │
     │                               │
     ▼                               │
┌─────────────────────┐              │
│ POST /api/messages  │              │
│ sender: buyer       │              │
│ receiver: lister    │              │
│ content: "Is this   │              │
│ still available?"   │              │
└─────────┬───────────┘              │
          │                          │
          │ triggers                 │
          ▼                          │
┌─────────────────────┐              │
│ POST /api/          │              │
│ notifications       │              │
│ user: lister        │              │
│ type: "message"     │              │
└─────────────────────┘              │
                                     │
                    Notification ────►
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │ GET /api/messages   │
                          │ ?user=lister        │
                          │ &conversation_with= │
                          │   buyer             │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │ POST /api/messages  │
                          │ (lister replies)    │
                          └─────────────────────┘
```

### 5. Admin Verification Workflow
```
┌─────────────────────┐
│  PENDING LISTINGS   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ GET /api/listings           │
│ ?status=pending             │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ GET /api/verification-docs  │
│ ?user_firebase_uid=xyz      │
└──────────┬──────────────────┘
           │
           ▼ Admin reviews documents
┌─────────────────────────────┐
│ PUT /api/verification-docs/ │
│ {doc_id}/verify             │
│ status: "verified"          │
└──────────┬──────────────────┘
           │
           │ Auto-updates
           ▼
┌─────────────────────────────┐
│ USERS.verification_status   │
│ = "verified"                │
└─────────────────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ PUT /api/listings/{id}      │
│ status: "verified"          │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ POST /api/notifications     │
│ user: lister                │
│ "Your listing is approved!" │
└─────────────────────────────┘
```

---

## Collection Sizes & Indexes

### Performance Optimizations

```
COLLECTION              INDEXES                        PURPOSE
──────────────────────────────────────────────────────────────────────
users                   firebase_uid (unique)         Fast user lookup
                        email                         Email search
                        role                          Filter by role

properties              property_id (unique)          Fast property lookup
                        property_type                 Filter by type
                        current_price                 Price range queries
                        (city + state)                Location searches

listings                listing_id (unique)           Fast listing lookup
                        property_id                   Find property's listing
                        lister_firebase_uid           Lister's listings
                        status                        Filter active/pending

verification_documents  document_id (unique)          Fast doc lookup
                        user_firebase_uid             User's docs
                        status                        Pending verifications

saved_listings          saved_id (unique)             Fast saved lookup
                        user_firebase_uid             User's saved items
                        (user + listing) unique       Prevent duplicates

property_comparisons    comparison_id (unique)        Fast comparison lookup
                        user_firebase_uid             User's comparisons

reviews                 review_id (unique)            Fast review lookup
                        target_id                     Get all reviews
                        (target_type + target_id)     Specific target reviews

messages                message_id (unique)           Fast message lookup
                        sender_firebase_uid           Sent messages
                        receiver_firebase_uid         Received messages
                        sent_at                       Chronological order

notifications           notification_id (unique)      Fast notification lookup
                        user_firebase_uid             User's notifications

audit_logs              log_id (unique)               Fast log lookup
                        user_firebase_uid             User's activities
                        timestamp                     Time-based queries
                        action                        Filter by action type
```

---

## Key Design Decisions

### 1. Embedded vs Referenced Data

**Embedded (within document):**
- `price_history[]` in Properties - Frequently accessed together, small array
- `location{}` in Properties - Always needed with property info
- `amenities[]` in Properties - Simple array, no separate collection needed

**Referenced (separate collections):**
- Listings → Properties - Many-to-one relationship
- Messages - Needs bi-directional queries (sender/receiver)
- Reviews - Can target multiple entities (properties/listers)

### 2. Firebase UID as Primary Key
- Avoids password storage in MongoDB
- Simplified authentication flow
- Firebase handles security, rate limiting, 2FA

### 3. Status Enums
Strict status values ensure data consistency:
- User verification: `not_submitted | pending | verified | rejected`
- Listing status: `pending | verified | active | hidden | rejected | expired`
- Message status: `unread | read`

### 4. Automatic Features
- **Price History**: Auto-tracked on price updates
- **View Count**: Auto-incremented on listing views
- **Timestamps**: Auto-generated on create/update
- **User Verification**: Auto-updated when identity_proof verified

---

## Scalability Considerations

### Current Design (MVP)
- ✅ Handles 10,000+ concurrent users
- ✅ Fast queries with proper indexes
- ✅ Embedded price history (efficient for < 100 entries)

### Future Enhancements (Production)
1. **Separate Price History Collection** - If properties have frequent price changes
2. **Geospatial Indexes** - For radius-based searches (lat/long)
3. **Full-Text Search** - MongoDB Atlas Search for property descriptions
4. **Read Replicas** - For high-traffic read operations
5. **Caching Layer** - Redis for frequently accessed listings
6. **Sharding** - Partition by location/property_type for massive scale

---

## Security Best Practices

### Implemented:
✅ Firebase UID (no password storage)
✅ Role-based user types
✅ Admin verification workflow
✅ Audit logging
✅ Unique constraints prevent duplicates

### Recommended for Production:
- JWT token verification middleware
- Rate limiting per user
- Input validation & sanitization
- HTTPS only
- Regular backup strategy
- Encrypted document storage (S3/Firebase Storage)

---

## Sample Queries Cheat Sheet

```javascript
// Find verified listers
db.users.find({ role: "lister", verification_status: "verified" })

// Get active listings in Austin
db.listings.aggregate([
  { $match: { status: "active" } },
  { $lookup: {
      from: "properties",
      localField: "property_id",
      foreignField: "property_id",
      as: "property"
    }},
  { $unwind: "$property" },
  { $match: { "property.location.city": "Austin" } }
])

// Find properties with price drops
db.properties.find({
  $expr: { $gt: [{ $size: "$price_history" }, 1] }
})

// Get user's activity summary
db.audit_logs.aggregate([
  { $match: { user_firebase_uid: "buyer-001" } },
  { $group: {
      _id: "$action",
      count: { $sum: 1 }
    }}
])

// Find most viewed listings
db.listings.find().sort({ views_count: -1 }).limit(10)

// Get lister's average rating
db.reviews.aggregate([
  { $match: { target_type: "lister", target_id: "lister-001" } },
  { $group: {
      _id: "$target_id",
      avgRating: { $avg: "$rating" },
      totalReviews: { $sum: 1 }
    }}
])
```
