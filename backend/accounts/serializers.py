from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, LoginAttempt


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'employee_id', 'phone_number', 'avatar', 'bio', 'date_of_birth',
            'hire_date', 'address_line_1', 'address_line_2', 'city', 'state',
            'postal_code', 'country', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relationship',
            'position', 'is_remote', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'is_verified', 'is_active', 'full_name', 'profile',
            'password', 'password_confirm', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'is_verified', 'created_at', 'updated_at')
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True},
        }
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def validate(self, attrs):
        if 'password' in attrs and 'password_confirm' in attrs:
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user
    
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for user lists"""
    full_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'is_active', 'department', 'position'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_department(self, obj):
        # Get primary department assignment
        assignment = obj.department_assignments.filter(is_primary=True, end_date__isnull=True).first()
        if assignment:
            return {
                'id': assignment.department.id,
                'name': assignment.department.name,
                'code': assignment.department.code
            }
        return None
    
    def get_position(self, obj):
        # Get current position
        assignment = obj.department_assignments.filter(is_primary=True, end_date__isnull=True).first()
        if assignment and assignment.position:
            return {
                'id': assignment.position.id,
                'title': assignment.position.title,
                'level': assignment.position.level
            }
        return None


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    current_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(style={'input_type': 'password'}, validators=[validate_password])
    new_password_confirm = serializers.CharField(style={'input_type': 'password'})
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'employee_id', 'phone_number', 'avatar', 'bio', 'date_of_birth',
            'address_line_1', 'address_line_2', 'city', 'state',
            'postal_code', 'country', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relationship',
            'position', 'is_remote'
        ]


class LoginAttemptSerializer(serializers.ModelSerializer):
    """Serializer for login attempts"""
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = LoginAttempt
        fields = [
            'id', 'user_email', 'ip_address', 'successful', 'attempted_at'
        ]
        read_only_fields = ('id', 'attempted_at')
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else 'Unknown'


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError('No active user found with this email address')
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs 