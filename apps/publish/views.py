from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.throttling import ScopedRateThrottle
from django.db import transaction
from utils.base_view import BaseAPIView as APIView
from utils.permission import IsAdmin, RolePermission, IsOwnerOrParentHierarchy
from .models import SocialPost, PostMediaFile, MediaDraft
from .serializers import SocialPostSerializer, SocialMediaSerializer, SocialPostCreateSerializer, MediaDraftSerializer
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from django.conf import settings
from apps.social.models import (
    SocialAccount, FacebookPage, FacebookPage, SocialPlatform, InstagramAccount, 
    )

from .utils.publish_Facebook_post import publish_fb_post, get_post_insights
from .utils.instagram_post import create_ig_post
from .utils.tiktok_post import get_tiktok_post_details
from .services.media_service import save_media_files
from .services.publish_service import publish_to_platforms, publish_post
from .services.post_generations import generate_caption, generate_hashtags, generate_image


app_id = settings.FACEBOOK_APP_ID
app_secret = settings.FACEBOOK_APP_SECRET


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    return None


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
        post = SocialPost.objects.filter(id=post_id, author=request.user).first()
        if not post:
            return self.error(
                message="Social post not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = SocialPostSerializer(post, many=False)
        return self.success(
            message="Social post fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )
        
    def patch(self, request, post_id):
        post = SocialPost.objects.filter(id=post_id, author=request.user).first()
        if not post:
            return self.error(
                message="Social post not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # if post.scheduled_at:
        #     serializer = SocialPostSerializer(post, data=request.data, partial=True)
        #     serializer.is_valid(raise_exception=True)
        #     serializer.save()
        #     return self.success(
        #         message="Social post updated successfully",
        #         status_code=status.HTTP_200_OK,
        #         data=serializer.data
        #     )
        if "is_published" not in request.data:
            return self.error(
                message="is_published is required in request body",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={
                    "is_published": [
                        "Send true to publish this post."
                    ]
                },
            )

        requested_publish_state = _coerce_bool(request.data.get("is_published"))
        if requested_publish_state is None:
            return self.error(
                message="Invalid is_published value",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={
                    "is_published": [
                        "Expected boolean true/false (or true/false string)."
                    ]
                },
            )

        if not requested_publish_state:
            return self.error(
                message="Unpublish is not supported from this endpoint",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={
                    "is_published": [
                        "Use is_published=true to publish."
                    ]
                },
            )

        if post.is_published:
            return self.success(
                message="Social post is already published",
                status_code=status.HTTP_200_OK,
                data={
                    "success": True,
                    "results": [],
                    "post_ids": post.post_ids or [],
                },
            )

        post.is_published = True
        res = publish_post(request.user, post)
        if isinstance(res, dict) and res.get("success"):
            post.save()
            return self.success(
                message="Social post published successfully",
                status_code=status.HTTP_200_OK,
                data=res
            )

        post.is_published = False
        post.save(update_fields=["is_published"])
        return self.error(
            message="Social post publishing failed",
            errors={"results": (res or {}).get("results", [])} if isinstance(res, dict) else None,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        
        
class PostInsightsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, post_id):
        try:
            post = SocialPost.objects.get(id=post_id)
            post_datas = []

            def _normalize_post_reference(post_ref):
                if isinstance(post_ref, list):
                    return post_ref[0] if post_ref else None
                if isinstance(post_ref, dict):
                    return (
                        post_ref.get("publish_id")
                        or post_ref.get("post_id")
                        or post_ref.get("video_id")
                        or post_ref.get("id")
                    )
                return post_ref

            for post_item in post.post_ids:
                platform = post_item.get("platform")
                post_ref = _normalize_post_reference(post_item.get("post_id"))
                if platform == "facebook":
                    insights = (
                        get_post_insights(post.page_access_token, post_ref)
                        if post.page_access_token and post_ref
                        else {"error": "Facebook token or post_id missing"}
                    )
                    post_datas.append({
                        "platform": platform,
                        "post_id": post_item.get("post_id"),
                        "insights": insights
                    })
                elif platform == "instagram":
                    post_datas.append({
                        "platform": platform,
                        "post_id": post_item.get("post_id"),
                        "insights": {
                            "message": "Instagram insights are not configured in this endpoint"
                        }
                    })
                elif platform == "tiktok":
                    tk_account = SocialAccount.objects.filter(
                        user=request.user,
                        platform="tiktok",
                    ).first()
                    tk_token = (
                        getattr(tk_account, "access_token", None)
                        or getattr(tk_account, "long_lived_token", None)
                        or getattr(tk_account, "user_access_token", None)
                    )
                    insights = get_tiktok_post_details(tk_token, post_ref)
                    post_datas.append({
                        "platform": platform,
                        "post_id": post_item.get("post_id"),
                        "insights": insights,
                    })
                else:
                    post_datas.append({
                        "platform": platform,
                        "post_id": post_item.get("post_id"),
                        "insights": {}
                    })
            return self.success(
                message="Post insights fetched successfully",
                status_code=status.HTTP_200_OK,
                data=post_datas
            )
        except Exception as e:
            return self.error(
                message="Post insights fetched failed",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={"detail": str(e)}
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
                media_urls.append(m.file.url)
            
            if pfm == "facebook":
                fb_page_id = request.data.get("fb_page_id")
                page = FacebookPage.objects.get(user=request.user, id=fb_page_id)
                platform_post_id, video_ids = publish_fb_post(
                    page.page_id,
                    page.page_access_token,
                    post.caption,
                    media_urls,
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
        if name == "caption":
            data_list = [
                'ecommerce', 'friendly', 'product_launch', 'brand_promotion', 'sale_offer', 'startup_update', 
                'local_business', 'news', 'event', 'education', 'healthcare', 'travel', 'food', 'entertainment',
                'sports', 'finance', 'technology',
            ]
        elif name == "hashtags":
            data_list = []
        elif name == "image":
            data_list = ["1:1", "3:4", "4:3", "9:16", "16:9"]
        return self.success(
            message="list fetched successfully",
            status_code=status.HTTP_200_OK,
            data=data_list
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
        elif name == "image":
            image = generate_image(
                caption=context,
                extra_prompt=request.data.get("extra_prompt", ""),
                aspect_ratio=request.data.get("aspect_ratio", "1:1")
            )
            if image:
                draft = MediaDraft.objects.create(
                    user=request.user,
                    file=image
                )
                data = MediaDraftSerializer(draft, many=False).data
                return self.success(
                    message="Image generated successfully",
                    status_code=status.HTTP_200_OK,
                    data=data
                )
            else:
                return self.error(
                    message="Image generation failed",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        else:
            return self.error(
                message=f"Page not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
            
class demoImage(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        draft = MediaDraft.objects.filter(user=request.user).first()
        if not draft:
            return self.error(
                message="No draft found",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return self.success(
            message="Image draft fetched successfully",
            status_code=status.HTTP_200_OK,
            data=MediaDraftSerializer(draft, many=False).data
        )
    

                


 





    



    
