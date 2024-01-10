from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from user.models import UserActivity, UserProfile, BenefitHistory, Ticket, TicketDepartment, TicketMessage, Referrer, UserAgent

User = get_user_model()

class MarketSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source='userprofile.avatar', read_only=True)
    f_name = serializers.CharField(source='userprofile.f_name', read_only=True)
    l_name = serializers.CharField(source='userprofile.l_name', read_only=True)
    referer_id=serializers.IntegerField(source='userprofile__referer_id', read_only=True)
    referer_email = serializers.SerializerMethodField(read_only=True)
    referer_username = serializers.SerializerMethodField(read_only=True)
    referer_avatar = serializers.SerializerMethodField(read_only=True)
    # referer_avatar = serializers.ImageField(source='userprofile.referer__avatar', read_only=True)  # Change this line to ImageField
    class Meta:
        model = User
        fields = ['id', 'avatar', 'username', 'f_name', 'l_name', 'email', 'password', 'status', 'email_verified_at', 'last_login_dt', 'last_login_ip', 'activation_code', 'note', 'forgot_password_code', 'referer_id', 'created_at', 'updated_at', 'referer_email', 'referer_username', 'referer_avatar']
        extra_kwargs = {
            'password': {'write_only': True}  # password field is write-only
        }
    def update(self, instance, validated_data):
        # Update the password if provided in the data
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)

        return super().update(instance, validated_data)
    def get_referer_avatar(self, instance):
        user_profile = UserProfile.objects.filter(user_id=instance.id).first()
        if user_profile.referer_id is not None:
            try:
                referer_user = User.objects.get(id=user_profile.referer_id)
                if hasattr(referer_user, 'userprofile'):
                    return self.context['request'].build_absolute_uri(referer_user.userprofile.avatar.url)
            except User.DoesNotExist:
                pass
        return None
    def get_referer_email(self, instance):
        user_profile = UserProfile.objects.filter(user_id=instance.id).first()
        if user_profile.referer_id is not None:
            try:
                referer_user = User.objects.get(id=user_profile.referer_id)
                return referer_user.email
            except User.DoesNotExist:
                pass
        return None
    def get_referer_username(self, instance):
        user_profile = UserProfile.objects.filter(user_id=instance.id).first()
        if user_profile.referer_id is not None:
            try:
                referer_user = User.objects.get(id=user_profile.referer_id)
                return referer_user.username
            except User.DoesNotExist:
                pass
        return None

class UserActivitySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = UserActivity
        fields = ['user', 'user_email', 'action', 'location', 'ip', 'level', 'created_at', 'updated_at']
 
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        
class BenefitHistorySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = BenefitHistory
        fields = ['user', 'user_email', 'benefit_rate', 'created_at', 'updated_at']

class TicketDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketDepartment
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(read_only=True)
    user_name = serializers.CharField(read_only=True)
    un_read_count = serializers.SerializerMethodField(read_only=True)
    user_email = serializers.EmailField(read_only=True)
    class Meta:
        model = Ticket
        fields = ['id', 'department', 'department_name', 'user_name', 'user_email', 'user', 'attach', 'attach_origin', 'subject', 'content', 'status', 'no', 'un_read_count', 'created_at', 'updated_at']
    def get_un_read_count(self, instance):
        un_read_count = TicketMessage.objects.filter(ticket_id=instance.id, is_read=False, type=0).count()
        return un_read_count

class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = '__all__'

class RerrerSerializer(serializers.ModelSerializer):
    referr_name = serializers.CharField(read_only=True)
    referr_country = serializers.CharField(read_only=True)
    class Meta:
        model = Referrer
        fields = ['id', 'referr_name', 'referr_country', 'referr', 'user']

class UserAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAgent
        fields = ['id', 'ip', 'browser_info', 'created_at']
