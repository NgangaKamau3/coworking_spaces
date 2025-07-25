import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.authentication.models import User
from apps.venues.models import Venue, Space
from apps.bookings.models import Booking

class Review(models.Model):
    """Post-booking feedback system"""
    
    REVIEW_STATUS = [
        ('pending', 'Pending Moderation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    ]
    
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='reviews')
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Rating components (1-5 scale)
    overall_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    cleanliness_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    wifi_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    noise_level_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    amenities_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Review content
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Moderation
    status = models.CharField(max_length=20, choices=REVIEW_STATUS, default='pending')
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_reviews')
    moderation_notes = models.TextField(blank=True)
    
    # Metadata
    is_anonymous = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['venue', 'status', 'created_at']),
            models.Index(fields=['overall_rating']),
        ]
        ordering = ['-created_at']
    
    def calculate_average_rating(self):
        """Calculate average of all rating components"""
        ratings = [
            self.overall_rating,
            self.cleanliness_rating,
            self.wifi_rating,
            self.noise_level_rating,
            self.amenities_rating
        ]
        return sum(ratings) / len(ratings)

class ReviewHelpful(models.Model):
    """Track helpful votes for reviews"""
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField()  # True for helpful, False for not helpful
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']

class VenueRating(models.Model):
    """Aggregated venue ratings"""
    
    venue = models.OneToOneField(Venue, on_delete=models.CASCADE, related_name='rating')
    
    # Aggregated ratings
    average_overall_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    average_cleanliness_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    average_wifi_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    average_noise_level_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    average_amenities_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Review counts
    total_reviews = models.PositiveIntegerField(default=0)
    five_star_count = models.PositiveIntegerField(default=0)
    four_star_count = models.PositiveIntegerField(default=0)
    three_star_count = models.PositiveIntegerField(default=0)
    two_star_count = models.PositiveIntegerField(default=0)
    one_star_count = models.PositiveIntegerField(default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def update_ratings(self):
        """Update aggregated ratings from approved reviews"""
        approved_reviews = Review.objects.filter(
            venue=self.venue,
            status='approved'
        )
        
        if not approved_reviews.exists():
            return
        
        # Calculate averages
        self.average_overall_rating = approved_reviews.aggregate(
            models.Avg('overall_rating')
        )['overall_rating__avg'] or 0
        
        self.average_cleanliness_rating = approved_reviews.aggregate(
            models.Avg('cleanliness_rating')
        )['cleanliness_rating__avg'] or 0
        
        self.average_wifi_rating = approved_reviews.aggregate(
            models.Avg('wifi_rating')
        )['wifi_rating__avg'] or 0
        
        self.average_noise_level_rating = approved_reviews.aggregate(
            models.Avg('noise_level_rating')
        )['noise_level_rating__avg'] or 0
        
        self.average_amenities_rating = approved_reviews.aggregate(
            models.Avg('amenities_rating')
        )['amenities_rating__avg'] or 0
        
        # Count by star rating
        self.total_reviews = approved_reviews.count()
        self.five_star_count = approved_reviews.filter(overall_rating=5).count()
        self.four_star_count = approved_reviews.filter(overall_rating=4).count()
        self.three_star_count = approved_reviews.filter(overall_rating=3).count()
        self.two_star_count = approved_reviews.filter(overall_rating=2).count()
        self.one_star_count = approved_reviews.filter(overall_rating=1).count()
        
        self.save()

class ReviewModerationRule(models.Model):
    """Automated review moderation rules"""
    
    RULE_TYPES = [
        ('keyword_filter', 'Keyword Filter'),
        ('sentiment_analysis', 'Sentiment Analysis'),
        ('length_check', 'Length Check'),
        ('profanity_filter', 'Profanity Filter'),
    ]
    
    rule_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    rule_name = models.CharField(max_length=100)
    rule_config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    # Actions
    auto_approve = models.BooleanField(default=False)
    auto_reject = models.BooleanField(default=False)
    flag_for_review = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def apply_rule(self, review):
        """Apply moderation rule to review"""
        if not self.is_active:
            return None
        
        if self.rule_type == 'keyword_filter':
            return self._apply_keyword_filter(review)
        elif self.rule_type == 'length_check':
            return self._apply_length_check(review)
        elif self.rule_type == 'profanity_filter':
            return self._apply_profanity_filter(review)
        
        return None
    
    def _apply_keyword_filter(self, review):
        """Apply keyword filtering"""
        keywords = self.rule_config.get('keywords', [])
        text = f"{review.title} {review.comment}".lower()
        
        for keyword in keywords:
            if keyword.lower() in text:
                if self.auto_reject:
                    return 'rejected'
                elif self.flag_for_review:
                    return 'flagged'
        
        return None
    
    def _apply_length_check(self, review):
        """Apply length validation"""
        min_length = self.rule_config.get('min_length', 10)
        max_length = self.rule_config.get('max_length', 1000)
        
        comment_length = len(review.comment)
        
        if comment_length < min_length or comment_length > max_length:
            if self.auto_reject:
                return 'rejected'
            elif self.flag_for_review:
                return 'flagged'
        
        return None
    
    def _apply_profanity_filter(self, review):
        """Apply profanity filtering"""
        # Implement profanity detection logic
        profane_words = self.rule_config.get('profane_words', [])
        text = f"{review.title} {review.comment}".lower()
        
        for word in profane_words:
            if word.lower() in text:
                if self.auto_reject:
                    return 'rejected'
                elif self.flag_for_review:
                    return 'flagged'
        
        return None