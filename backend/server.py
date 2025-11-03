from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal
from datetime import datetime, timezone
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== ENUMS ====================
class UserRole(str, Enum):
    VISITOR = "visitor"
    BUYER = "buyer"
    RENTER = "renter"
    LISTER = "lister"
    ADMIN = "admin"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    NOT_SUBMITTED = "not_submitted"

class ListingStatus(str, Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PropertyType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LAND = "land"
    RENTAL = "rental"

class MessageStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"

# ==================== MODELS ====================

# User Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    firebase_uid: str
    email: EmailStr
    name: str
    role: UserRole
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.NOT_SUBMITTED
    two_factor_enabled: bool = False
    is_suspended: bool = False
    is_banned: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    firebase_uid: str
    email: EmailStr
    name: str
    role: UserRole
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    two_factor_enabled: Optional[bool] = None

# Property Models
class Location(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class PriceHistory(BaseModel):
    price: float
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None

class Property(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    property_id: str
    title: str
    description: str
    property_type: PropertyType
    current_price: float
    price_history: List[PriceHistory] = []
    location: Location
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    area_sqft: Optional[float] = None
    year_built: Optional[int] = None
    amenities: List[str] = []
    images: List[str] = []
    documents: List[str] = []
    virtual_tour_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PropertyCreate(BaseModel):
    property_id: str
    title: str
    description: str
    property_type: PropertyType
    current_price: float
    location: Location
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    area_sqft: Optional[float] = None
    year_built: Optional[int] = None
    amenities: List[str] = []
    images: List[str] = []
    documents: List[str] = []
    virtual_tour_url: Optional[str] = None

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    current_price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    area_sqft: Optional[float] = None
    amenities: Optional[List[str]] = None
    images: Optional[List[str]] = None
    documents: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None

# Listing Models
class Listing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    listing_id: str
    property_id: str
    lister_firebase_uid: str
    status: ListingStatus = ListingStatus.PENDING
    views_count: int = 0
    verified_at: Optional[datetime] = None
    verified_by_admin_uid: Optional[str] = None
    rejection_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ListingCreate(BaseModel):
    listing_id: str
    property_id: str
    lister_firebase_uid: str
    expires_at: Optional[datetime] = None

class ListingUpdate(BaseModel):
    status: Optional[ListingStatus] = None
    rejection_reason: Optional[str] = None
    expires_at: Optional[datetime] = None

# Verification Document Models
class VerificationDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    document_id: str
    user_firebase_uid: str
    document_type: str  # e.g., "identity_proof", "property_ownership", "business_license"
    document_url: str
    status: VerificationStatus = VerificationStatus.PENDING
    verified_at: Optional[datetime] = None
    verified_by_admin_uid: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VerificationDocumentCreate(BaseModel):
    document_id: str
    user_firebase_uid: str
    document_type: str
    document_url: str

# Saved Listing Models
class SavedListing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    saved_id: str
    user_firebase_uid: str
    listing_id: str
    notes: Optional[str] = None
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SavedListingCreate(BaseModel):
    saved_id: str
    user_firebase_uid: str
    listing_id: str
    notes: Optional[str] = None

# Property Comparison Models
class PropertyComparison(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    comparison_id: str
    user_firebase_uid: str
    property_ids: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PropertyComparisonCreate(BaseModel):
    comparison_id: str
    user_firebase_uid: str
    property_ids: List[str]

# Review Models
class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    review_id: str
    reviewer_firebase_uid: str
    target_type: Literal["property", "lister"]
    target_id: str  # property_id or lister_firebase_uid
    rating: float  # 1-5
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewCreate(BaseModel):
    review_id: str
    reviewer_firebase_uid: str
    target_type: Literal["property", "lister"]
    target_id: str
    rating: float
    comment: str

# Message Models
class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    message_id: str
    sender_firebase_uid: str
    receiver_firebase_uid: str
    listing_id: Optional[str] = None
    subject: Optional[str] = None
    content: str
    status: MessageStatus = MessageStatus.UNREAD
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = None

class MessageCreate(BaseModel):
    message_id: str
    sender_firebase_uid: str
    receiver_firebase_uid: str
    listing_id: Optional[str] = None
    subject: Optional[str] = None
    content: str

# Notification Models
class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    notification_id: str
    user_firebase_uid: Optional[str] = None  # None for broadcast notifications
    title: str
    message: str
    notification_type: str  # e.g., "system", "listing_update", "message", "verification"
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NotificationCreate(BaseModel):
    notification_id: str
    user_firebase_uid: Optional[str] = None
    title: str
    message: str
    notification_type: str

# Audit Log Models
class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    log_id: str
    user_firebase_uid: Optional[str] = None
    action: str  # e.g., "user_login", "property_viewed", "listing_created", "search_performed"
    resource_type: Optional[str] = None  # e.g., "property", "user", "listing"
    resource_id: Optional[str] = None
    metadata: Optional[dict] = {}  # Additional data like search filters, IP address, etc.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLogCreate(BaseModel):
    log_id: str
    user_firebase_uid: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Optional[dict] = {}

# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Real Estate Listing API"}

# ===== USER ROUTES =====
@api_router.post("/users", response_model=User)
async def create_user(user: UserCreate):
    existing_user = await db.users.find_one({"firebase_uid": user.firebase_uid}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_obj = User(**user.model_dump())
    doc = user_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.users.insert_one(doc)
    return user_obj

@api_router.get("/users/{firebase_uid}", response_model=User)
async def get_user(firebase_uid: str):
    user = await db.users.find_one({"firebase_uid": firebase_uid}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if isinstance(user['created_at'], str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    if isinstance(user['updated_at'], str):
        user['updated_at'] = datetime.fromisoformat(user['updated_at'])
    
    return user

@api_router.put("/users/{firebase_uid}", response_model=User)
async def update_user(firebase_uid: str, user_update: UserUpdate):
    user = await db.users.find_one({"firebase_uid": firebase_uid}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one({"firebase_uid": firebase_uid}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"firebase_uid": firebase_uid}, {"_id": 0})
    if isinstance(updated_user['created_at'], str):
        updated_user['created_at'] = datetime.fromisoformat(updated_user['created_at'])
    if isinstance(updated_user['updated_at'], str):
        updated_user['updated_at'] = datetime.fromisoformat(updated_user['updated_at'])
    
    return updated_user

@api_router.get("/users", response_model=List[User])
async def get_users(role: Optional[UserRole] = None, limit: int = Query(100, le=1000)):
    query = {"role": role} if role else {}
    users = await db.users.find(query, {"_id": 0}).to_list(limit)
    
    for user in users:
        if isinstance(user['created_at'], str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if isinstance(user['updated_at'], str):
            user['updated_at'] = datetime.fromisoformat(user['updated_at'])
    
    return users

# ===== PROPERTY ROUTES =====
@api_router.post("/properties", response_model=Property)
async def create_property(property: PropertyCreate):
    existing = await db.properties.find_one({"property_id": property.property_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Property ID already exists")
    
    # Create initial price history
    initial_price_history = [PriceHistory(price=property.current_price, reason="Initial listing")]
    
    property_obj = Property(**property.model_dump(), price_history=initial_price_history)
    doc = property_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    for ph in doc['price_history']:
        ph['changed_at'] = ph['changed_at'].isoformat()
    
    await db.properties.insert_one(doc)
    return property_obj

@api_router.get("/properties/{property_id}", response_model=Property)
async def get_property(property_id: str):
    property = await db.properties.find_one({"property_id": property_id}, {"_id": 0})
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if isinstance(property['created_at'], str):
        property['created_at'] = datetime.fromisoformat(property['created_at'])
    if isinstance(property['updated_at'], str):
        property['updated_at'] = datetime.fromisoformat(property['updated_at'])
    for ph in property.get('price_history', []):
        if isinstance(ph['changed_at'], str):
            ph['changed_at'] = datetime.fromisoformat(ph['changed_at'])
    
    return property

@api_router.put("/properties/{property_id}", response_model=Property)
async def update_property(property_id: str, property_update: PropertyUpdate):
    property = await db.properties.find_one({"property_id": property_id}, {"_id": 0})
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    update_data = {k: v for k, v in property_update.model_dump().items() if v is not None}
    
    # Handle price change
    if 'current_price' in update_data and update_data['current_price'] != property['current_price']:
        new_price_entry = PriceHistory(price=update_data['current_price'], reason="Price updated")
        price_dict = new_price_entry.model_dump()
        price_dict['changed_at'] = price_dict['changed_at'].isoformat()
        await db.properties.update_one(
            {"property_id": property_id},
            {"$push": {"price_history": price_dict}}
        )
    
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.properties.update_one({"property_id": property_id}, {"$set": update_data})
    
    updated_property = await db.properties.find_one({"property_id": property_id}, {"_id": 0})
    if isinstance(updated_property['created_at'], str):
        updated_property['created_at'] = datetime.fromisoformat(updated_property['created_at'])
    if isinstance(updated_property['updated_at'], str):
        updated_property['updated_at'] = datetime.fromisoformat(updated_property['updated_at'])
    for ph in updated_property.get('price_history', []):
        if isinstance(ph['changed_at'], str):
            ph['changed_at'] = datetime.fromisoformat(ph['changed_at'])
    
    return updated_property

@api_router.get("/properties", response_model=List[Property])
async def get_properties(
    property_type: Optional[PropertyType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    city: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    query = {}
    if property_type:
        query["property_type"] = property_type
    if min_price is not None or max_price is not None:
        query["current_price"] = {}
        if min_price is not None:
            query["current_price"]["$gte"] = min_price
        if max_price is not None:
            query["current_price"]["$lte"] = max_price
    if city:
        query["location.city"] = {"$regex": city, "$options": "i"}
    
    properties = await db.properties.find(query, {"_id": 0}).to_list(limit)
    
    for property in properties:
        if isinstance(property['created_at'], str):
            property['created_at'] = datetime.fromisoformat(property['created_at'])
        if isinstance(property['updated_at'], str):
            property['updated_at'] = datetime.fromisoformat(property['updated_at'])
        for ph in property.get('price_history', []):
            if isinstance(ph['changed_at'], str):
                ph['changed_at'] = datetime.fromisoformat(ph['changed_at'])
    
    return properties

@api_router.delete("/properties/{property_id}")
async def delete_property(property_id: str):
    result = await db.properties.delete_one({"property_id": property_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": "Property deleted successfully"}

# ===== LISTING ROUTES =====
@api_router.post("/listings", response_model=Listing)
async def create_listing(listing: ListingCreate):
    # Verify property exists
    property = await db.properties.find_one({"property_id": listing.property_id}, {"_id": 0})
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Verify lister exists
    user = await db.users.find_one({"firebase_uid": listing.lister_firebase_uid}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Lister not found")
    
    listing_obj = Listing(**listing.model_dump())
    doc = listing_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    if doc.get('verified_at'):
        doc['verified_at'] = doc['verified_at'].isoformat()
    if doc.get('expires_at'):
        doc['expires_at'] = doc['expires_at'].isoformat()
    
    await db.listings.insert_one(doc)
    return listing_obj

@api_router.get("/listings/{listing_id}", response_model=Listing)
async def get_listing(listing_id: str):
    listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Increment view count
    await db.listings.update_one({"listing_id": listing_id}, {"$inc": {"views_count": 1}})
    
    if isinstance(listing['created_at'], str):
        listing['created_at'] = datetime.fromisoformat(listing['created_at'])
    if isinstance(listing['updated_at'], str):
        listing['updated_at'] = datetime.fromisoformat(listing['updated_at'])
    if listing.get('verified_at') and isinstance(listing['verified_at'], str):
        listing['verified_at'] = datetime.fromisoformat(listing['verified_at'])
    if listing.get('expires_at') and isinstance(listing['expires_at'], str):
        listing['expires_at'] = datetime.fromisoformat(listing['expires_at'])
    
    return listing

@api_router.put("/listings/{listing_id}", response_model=Listing)
async def update_listing(listing_id: str, listing_update: ListingUpdate):
    listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    update_data = {k: v for k, v in listing_update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Handle verification
    if update_data.get('status') == ListingStatus.VERIFIED:
        update_data['verified_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.listings.update_one({"listing_id": listing_id}, {"$set": update_data})
    
    updated_listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if isinstance(updated_listing['created_at'], str):
        updated_listing['created_at'] = datetime.fromisoformat(updated_listing['created_at'])
    if isinstance(updated_listing['updated_at'], str):
        updated_listing['updated_at'] = datetime.fromisoformat(updated_listing['updated_at'])
    if updated_listing.get('verified_at') and isinstance(updated_listing['verified_at'], str):
        updated_listing['verified_at'] = datetime.fromisoformat(updated_listing['verified_at'])
    if updated_listing.get('expires_at') and isinstance(updated_listing['expires_at'], str):
        updated_listing['expires_at'] = datetime.fromisoformat(updated_listing['expires_at'])
    
    return updated_listing

@api_router.get("/listings", response_model=List[Listing])
async def get_listings(
    status: Optional[ListingStatus] = None,
    lister_firebase_uid: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    query = {}
    if status:
        query["status"] = status
    if lister_firebase_uid:
        query["lister_firebase_uid"] = lister_firebase_uid
    
    listings = await db.listings.find(query, {"_id": 0}).to_list(limit)
    
    for listing in listings:
        if isinstance(listing['created_at'], str):
            listing['created_at'] = datetime.fromisoformat(listing['created_at'])
        if isinstance(listing['updated_at'], str):
            listing['updated_at'] = datetime.fromisoformat(listing['updated_at'])
        if listing.get('verified_at') and isinstance(listing['verified_at'], str):
            listing['verified_at'] = datetime.fromisoformat(listing['verified_at'])
        if listing.get('expires_at') and isinstance(listing['expires_at'], str):
            listing['expires_at'] = datetime.fromisoformat(listing['expires_at'])
    
    return listings

# ===== VERIFICATION DOCUMENT ROUTES =====
@api_router.post("/verification-documents", response_model=VerificationDocument)
async def create_verification_document(doc: VerificationDocumentCreate):
    doc_obj = VerificationDocument(**doc.model_dump())
    doc_dict = doc_obj.model_dump()
    doc_dict['created_at'] = doc_dict['created_at'].isoformat()
    if doc_dict.get('verified_at'):
        doc_dict['verified_at'] = doc_dict['verified_at'].isoformat()
    
    await db.verification_documents.insert_one(doc_dict)
    return doc_obj

@api_router.get("/verification-documents/{document_id}", response_model=VerificationDocument)
async def get_verification_document(document_id: str):
    doc = await db.verification_documents.find_one({"document_id": document_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if isinstance(doc['created_at'], str):
        doc['created_at'] = datetime.fromisoformat(doc['created_at'])
    if doc.get('verified_at') and isinstance(doc['verified_at'], str):
        doc['verified_at'] = datetime.fromisoformat(doc['verified_at'])
    
    return doc

@api_router.get("/verification-documents", response_model=List[VerificationDocument])
async def get_verification_documents(
    user_firebase_uid: Optional[str] = None,
    status: Optional[VerificationStatus] = None,
    limit: int = Query(100, le=1000)
):
    query = {}
    if user_firebase_uid:
        query["user_firebase_uid"] = user_firebase_uid
    if status:
        query["status"] = status
    
    docs = await db.verification_documents.find(query, {"_id": 0}).to_list(limit)
    
    for doc in docs:
        if isinstance(doc['created_at'], str):
            doc['created_at'] = datetime.fromisoformat(doc['created_at'])
        if doc.get('verified_at') and isinstance(doc['verified_at'], str):
            doc['verified_at'] = datetime.fromisoformat(doc['verified_at'])
    
    return docs

@api_router.put("/verification-documents/{document_id}/verify")
async def verify_document(document_id: str, admin_uid: str, status: VerificationStatus, rejection_reason: Optional[str] = None):
    doc = await db.verification_documents.find_one({"document_id": document_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = {
        "status": status,
        "verified_by_admin_uid": admin_uid,
        "verified_at": datetime.now(timezone.utc).isoformat()
    }
    
    if rejection_reason:
        update_data["rejection_reason"] = rejection_reason
    
    await db.verification_documents.update_one({"document_id": document_id}, {"$set": update_data})
    
    # Update user verification status if identity proof is verified
    if status == VerificationStatus.VERIFIED and doc['document_type'] == "identity_proof":
        await db.users.update_one(
            {"firebase_uid": doc['user_firebase_uid']},
            {"$set": {"verification_status": VerificationStatus.VERIFIED}}
        )
    
    return {"message": "Document verification updated"}

# ===== SAVED LISTING ROUTES =====
@api_router.post("/saved-listings", response_model=SavedListing)
async def save_listing(saved: SavedListingCreate):
    # Check if already saved
    existing = await db.saved_listings.find_one({
        "user_firebase_uid": saved.user_firebase_uid,
        "listing_id": saved.listing_id
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Listing already saved")
    
    saved_obj = SavedListing(**saved.model_dump())
    doc = saved_obj.model_dump()
    doc['saved_at'] = doc['saved_at'].isoformat()
    
    await db.saved_listings.insert_one(doc)
    return saved_obj

@api_router.get("/saved-listings", response_model=List[SavedListing])
async def get_saved_listings(user_firebase_uid: str, limit: int = Query(100, le=1000)):
    saved = await db.saved_listings.find({"user_firebase_uid": user_firebase_uid}, {"_id": 0}).to_list(limit)
    
    for item in saved:
        if isinstance(item['saved_at'], str):
            item['saved_at'] = datetime.fromisoformat(item['saved_at'])
    
    return saved

@api_router.delete("/saved-listings/{saved_id}")
async def remove_saved_listing(saved_id: str):
    result = await db.saved_listings.delete_one({"saved_id": saved_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saved listing not found")
    return {"message": "Saved listing removed"}

# ===== PROPERTY COMPARISON ROUTES =====
@api_router.post("/comparisons", response_model=PropertyComparison)
async def create_comparison(comparison: PropertyComparisonCreate):
    comparison_obj = PropertyComparison(**comparison.model_dump())
    doc = comparison_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.property_comparisons.insert_one(doc)
    return comparison_obj

@api_router.get("/comparisons", response_model=List[PropertyComparison])
async def get_comparisons(user_firebase_uid: str, limit: int = Query(100, le=1000)):
    comparisons = await db.property_comparisons.find({"user_firebase_uid": user_firebase_uid}, {"_id": 0}).to_list(limit)
    
    for comp in comparisons:
        if isinstance(comp['created_at'], str):
            comp['created_at'] = datetime.fromisoformat(comp['created_at'])
    
    return comparisons

@api_router.delete("/comparisons/{comparison_id}")
async def delete_comparison(comparison_id: str):
    result = await db.property_comparisons.delete_one({"comparison_id": comparison_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return {"message": "Comparison deleted"}

# ===== REVIEW ROUTES =====
@api_router.post("/reviews", response_model=Review)
async def create_review(review: ReviewCreate):
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    review_obj = Review(**review.model_dump())
    doc = review_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.reviews.insert_one(doc)
    return review_obj

@api_router.get("/reviews", response_model=List[Review])
async def get_reviews(
    target_type: Optional[Literal["property", "lister"]] = None,
    target_id: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    query = {}
    if target_type:
        query["target_type"] = target_type
    if target_id:
        query["target_id"] = target_id
    
    reviews = await db.reviews.find(query, {"_id": 0}).to_list(limit)
    
    for review in reviews:
        if isinstance(review['created_at'], str):
            review['created_at'] = datetime.fromisoformat(review['created_at'])
        if isinstance(review['updated_at'], str):
            review['updated_at'] = datetime.fromisoformat(review['updated_at'])
    
    return reviews

@api_router.delete("/reviews/{review_id}")
async def delete_review(review_id: str):
    result = await db.reviews.delete_one({"review_id": review_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted"}

# ===== MESSAGE ROUTES =====
@api_router.post("/messages", response_model=Message)
async def send_message(message: MessageCreate):
    message_obj = Message(**message.model_dump())
    doc = message_obj.model_dump()
    doc['sent_at'] = doc['sent_at'].isoformat()
    if doc.get('read_at'):
        doc['read_at'] = doc['read_at'].isoformat()
    
    await db.messages.insert_one(doc)
    return message_obj

@api_router.get("/messages", response_model=List[Message])
async def get_messages(
    user_firebase_uid: str,
    conversation_with: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    if conversation_with:
        query = {
            "$or": [
                {"sender_firebase_uid": user_firebase_uid, "receiver_firebase_uid": conversation_with},
                {"sender_firebase_uid": conversation_with, "receiver_firebase_uid": user_firebase_uid}
            ]
        }
    else:
        query = {
            "$or": [
                {"sender_firebase_uid": user_firebase_uid},
                {"receiver_firebase_uid": user_firebase_uid}
            ]
        }
    
    messages = await db.messages.find(query, {"_id": 0}).sort("sent_at", -1).to_list(limit)
    
    for msg in messages:
        if isinstance(msg['sent_at'], str):
            msg['sent_at'] = datetime.fromisoformat(msg['sent_at'])
        if msg.get('read_at') and isinstance(msg['read_at'], str):
            msg['read_at'] = datetime.fromisoformat(msg['read_at'])
    
    return messages

@api_router.put("/messages/{message_id}/read")
async def mark_message_read(message_id: str):
    result = await db.messages.update_one(
        {"message_id": message_id},
        {"$set": {"status": MessageStatus.READ, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {"message": "Message marked as read"}

# ===== NOTIFICATION ROUTES =====
@api_router.post("/notifications", response_model=Notification)
async def create_notification(notification: NotificationCreate):
    notification_obj = Notification(**notification.model_dump())
    doc = notification_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.notifications.insert_one(doc)
    return notification_obj

@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(user_firebase_uid: str, limit: int = Query(100, le=1000)):
    # Get user-specific and broadcast notifications
    query = {
        "$or": [
            {"user_firebase_uid": user_firebase_uid},
            {"user_firebase_uid": None}
        ]
    }
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    for notif in notifications:
        if isinstance(notif['created_at'], str):
            notif['created_at'] = datetime.fromisoformat(notif['created_at'])
    
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    result = await db.notifications.update_one(
        {"notification_id": notification_id},
        {"$set": {"is_read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

# ===== AUDIT LOG ROUTES =====
@api_router.post("/audit-logs", response_model=AuditLog)
async def create_audit_log(log: AuditLogCreate):
    log_obj = AuditLog(**log.model_dump())
    doc = log_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.audit_logs.insert_one(doc)
    return log_obj

@api_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    user_firebase_uid: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    query = {}
    if user_firebase_uid:
        query["user_firebase_uid"] = user_firebase_uid
    if action:
        query["action"] = action
    if resource_type:
        query["resource_type"] = resource_type
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    
    for log in logs:
        if isinstance(log['timestamp'], str):
            log['timestamp'] = datetime.fromisoformat(log['timestamp'])
    
    return logs

# ===== ADMIN ROUTES =====
@api_router.put("/admin/users/{firebase_uid}/suspend")
async def suspend_user(firebase_uid: str, is_suspended: bool):
    result = await db.users.update_one(
        {"firebase_uid": firebase_uid},
        {"$set": {"is_suspended": is_suspended}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    action = "suspended" if is_suspended else "unsuspended"
    return {"message": f"User {action}"}

@api_router.put("/admin/users/{firebase_uid}/ban")
async def ban_user(firebase_uid: str, is_banned: bool):
    result = await db.users.update_one(
        {"firebase_uid": firebase_uid},
        {"$set": {"is_banned": is_banned}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    action = "banned" if is_banned else "unbanned"
    return {"message": f"User {action}"}

@api_router.get("/admin/analytics")
async def get_analytics():
    total_users = await db.users.count_documents({})
    total_properties = await db.properties.count_documents({})
    total_listings = await db.listings.count_documents({})
    active_listings = await db.listings.count_documents({"status": ListingStatus.ACTIVE})
    pending_verifications = await db.verification_documents.count_documents({"status": VerificationStatus.PENDING})
    
    return {
        "total_users": total_users,
        "total_properties": total_properties,
        "total_listings": total_listings,
        "active_listings": active_listings,
        "pending_verifications": pending_verifications
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_indexes():
    """Create database indexes for better query performance"""
    # Users indexes
    await db.users.create_index("firebase_uid", unique=True)
    await db.users.create_index("email")
    await db.users.create_index("role")
    
    # Properties indexes
    await db.properties.create_index("property_id", unique=True)
    await db.properties.create_index("property_type")
    await db.properties.create_index("current_price")
    await db.properties.create_index([("location.city", 1), ("location.state", 1)])
    
    # Listings indexes
    await db.listings.create_index("listing_id", unique=True)
    await db.listings.create_index("property_id")
    await db.listings.create_index("lister_firebase_uid")
    await db.listings.create_index("status")
    
    # Verification documents indexes
    await db.verification_documents.create_index("document_id", unique=True)
    await db.verification_documents.create_index("user_firebase_uid")
    await db.verification_documents.create_index("status")
    
    # Saved listings indexes
    await db.saved_listings.create_index("saved_id", unique=True)
    await db.saved_listings.create_index("user_firebase_uid")
    await db.saved_listings.create_index([("user_firebase_uid", 1), ("listing_id", 1)], unique=True)
    
    # Property comparisons indexes
    await db.property_comparisons.create_index("comparison_id", unique=True)
    await db.property_comparisons.create_index("user_firebase_uid")
    
    # Reviews indexes
    await db.reviews.create_index("review_id", unique=True)
    await db.reviews.create_index("target_id")
    await db.reviews.create_index([("target_type", 1), ("target_id", 1)])
    
    # Messages indexes
    await db.messages.create_index("message_id", unique=True)
    await db.messages.create_index("sender_firebase_uid")
    await db.messages.create_index("receiver_firebase_uid")
    await db.messages.create_index("sent_at")
    
    # Notifications indexes
    await db.notifications.create_index("notification_id", unique=True)
    await db.notifications.create_index("user_firebase_uid")
    
    # Audit logs indexes
    await db.audit_logs.create_index("log_id", unique=True)
    await db.audit_logs.create_index("user_firebase_uid")
    await db.audit_logs.create_index("timestamp")
    await db.audit_logs.create_index("action")
    
    logger.info("Database indexes created successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()