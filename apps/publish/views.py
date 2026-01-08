from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.throttling import ScopedRateThrottle
from django.db import transaction
from utils.base_view import BaseAPIView as APIView
from utils.permission import IsAdmin, RolePermission, IsOwnerOrParentHierarchy
from .models import SocialPost, PostMediaFile
from .serializers import SocialPostSerializer, SocialMediaSerializer, SocialPostCreateSerializer
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from django.conf import settings
from apps.social.models import (
    SocialAccount, FacebookPage, FacebookPage, SocialPlatform, InstagramAccount
    )

from .utils.publish_Facebook_post import publish_fb_post
from .utils.instagram_post import create_ig_post
from .services.media_service import save_media_files
from .services.publish_service import publish_to_platforms, publish_post
from .services.post_generations import generate_caption, generate_hashtags


app_id = settings.FACEBOOK_APP_ID
app_secret = settings.FACEBOOK_APP_SECRET

class SocialPostView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_post"

    
    
    def get(self, request):
        posts = SocialPost.objects.filter(author=request.user).order_by("-created_at")
        serializer = SocialPostSerializer(posts, many=True)
        return self.success(
            message="Social post fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )

    def post(self, request):
        serializer = SocialPostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        platform_ids = data.pop("platforms")

        platforms = SocialPlatform.objects.filter(
            id__in=platform_ids,
            is_active=True
        )

        if not platforms.exists():
            return self.error(
                message="No valid platforms found",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            post = SocialPost.objects.create(
                author=request.user,
                **data
            )
            post.platforms.set(platforms)

            save_media_files(request, post)

            media_urls = [
                request.build_absolute_uri(media.file.url)
                for media in post.media.all()
            ]

            post_ids = publish_to_platforms(
                request.user, post, platforms, media_urls
            )

            post.post_ids = post_ids
            post.save(update_fields=["post_ids"])

        return self.success(
            message="Social post created successfully",
            status_code=status.HTTP_201_CREATED,
            data={"post_id": post.id, "platform_posts": post_ids}
        )
        
class SocialPostdetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, post_id):
        post = SocialPost.objects.get(id=post_id)
        serializer = SocialPostSerializer(post, many=False)
        return self.success(
            message="Social post fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )
        
    def patch(self, request, post_id):
        post = SocialPost.objects.get(id=post_id)
        # if post.scheduled_at:
        #     serializer = SocialPostSerializer(post, data=request.data, partial=True)
        #     serializer.is_valid(raise_exception=True)
        #     serializer.save()
        #     return self.success(
        #         message="Social post updated successfully",
        #         status_code=status.HTTP_200_OK,
        #         data=serializer.data
        #     )
        if request.data.get("is_published") and not post.is_published:
            post.is_published = True
            res = publish_post(request.user, post)
            if res:
                post.save()
                return self.success(
                    message="Social post published successfully",
                    status_code=status.HTTP_200_OK,
                    data=res
                )
            else:
                return self.error(
                    message="Social post publishing failed",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        
        return self.error(
            message="Social post updating failed",
            status_code=status.HTTP_400_BAD_REQUEST,
            data={"error": "Invalid data"}
        )

class SocialMediaGalleryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_post"

    def get(self, request):
        media = PostMediaFile.objects.filter(post__author=request.user)
        serializer = SocialMediaSerializer(media, many=True)
        return self.success(
            message="Social media fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )
    

class SocialPostPublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_post"

    def get(self, request):
        post = SocialPost.objects.filter(author=request.user, is_published=True)
        serializer = SocialPostSerializer(post, many=True)
        return self.success(
            message="Social post publish fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )
    
    def post(self, request):
        p_id = request.data.get("post_id")
        pfm = request.data.get("platform")
        
        try:
            post = SocialPost.objects.get(id=p_id)
            if post.is_published:
                return self.error(
                    message="Post is already published",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            media_urls = []
            for m in post.media.all():
                media_urls.append(f"{request.build_absolute_uri(m.file.url)}")
            
            if pfm == "facebook":
                fb_page_id = request.data.get("fb_page_id")
                page = FacebookPage.objects.get(user=request.user, id=fb_page_id)
                platform_post_id = publish_fb_post(
                    page.page_id,
                    page.page_access_token,
                    post.caption,
                    media_urls
                )
                post.post_id = platform_post_id
                post.is_published = True
                post.save()
            return self.success(
                message="Social post published successfully",
                status_code=status.HTTP_200_OK,
                data={}
            )
        except Exception as e:
            return self.error(
                message="Invalid data",
                errors={"detail": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
class SocialPlatformListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = []
        platforms = SocialAccount.objects.filter(user=request.user)
        for platform in platforms:
            data.append({
                'id': platform.id,
                'platform': platform.platform,
            })

        return self.success(
            message="Platform list fetched successfully",
            status_code=status.HTTP_200_OK,
            data=data
        )
        
class PlatformPageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        platform = request.GET.get('platform')
        data = []
        if platform == 'facebook':
            pages = FacebookPage.objects.filter(user=request.user)
            for page in pages:
                data.append({
                    'id': page.id,
                    'name': page.page_name,
                })

        return self.success(
            message="Page list fetched successfully",
            status_code=status.HTTP_200_OK,
            data=data
        )
        
        
class GeneratePostCaption(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, name):
        
        type_list = [
            'ecommerce',
            'friendly',
            'product_launch',
            'brand_promotion',
            'sale_offer',
            'startup_update',
            'local_business',
            'news',
            'event',
            'education',
            'healthcare',
            'travel',
            'food',
            'entertainment',
            'sports',
            'finance',
            'technology',
        ]
        return self.success(
            message="Generate post type list fetched successfully",
            status_code=status.HTTP_200_OK,
            data=type_list
        )
    
    def post(self, request, name):
        context = request.data.get("context")
        if not context:
            return self.error(
                message=f"Generate post {name} failed",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if name == "caption":
            caption = generate_caption(
                context=context,
                post_type=request.data.get("post_type"),
                max_length=request.data.get("max_length", 180)
            )
            return self.success(
                message="Caption generated successfully",
                status_code=status.HTTP_200_OK,
                data={"caption": caption}
            )
        elif name == "hashtags":
            hashtags = generate_hashtags(
                caption=context,
                max_hashtags=request.data.get("max_hashtags", 5)
            )
            return self.success(
                message="Hashtags generated successfully",
                status_code=status.HTTP_200_OK,
                data={"hashtags": hashtags}
            )
        else:
            return self.error(
                message=f"Page not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
    

                


 





    



    
