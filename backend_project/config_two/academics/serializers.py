from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Branch, Group, Subject, Lesson, BranchMember
from students.models import Student
from users.models import CustomUser

class GroupSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class SubjectSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'phone', 'email', 'status']

class SubjectSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='subject-detail', read_only=True)
    
    class Meta:
        model = Subject
        fields = ['id', 'url', 'name', 'status']

class GroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail', read_only=True)
    student_count = serializers.IntegerField(source='annotated_student_count', read_only=True)
    students = serializers.StringRelatedField(many=True, read_only=True) 
    
    class Meta:
        model = Group
        fields = ['id', 'url', 'name', 'status', 'students', 'student_count']


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail', read_only=True)
    student_count = serializers.IntegerField(source='students.count', read_only=True)
    students = serializers.StringRelatedField(many=True, read_only=True) 
    
    student_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Student.objects.all(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Group
        fields = ['id', 'url', 'name', 'status', 'students', 'student_count', 'student_ids']

    def _get_branch(self):
        branch = self.context.get('branch')
        if not branch and self.instance and hasattr(self.instance, 'branch'):
            branch = self.instance.branch
        if not branch and 'view' in self.context and 'pk' in self.context['view'].kwargs:
            try:
                branch = Branch.objects.get(pk=self.context['view'].kwargs['pk'])
            except Branch.DoesNotExist:
                pass
        return branch

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        branch = self._get_branch()
        if branch:
            self.fields['student_ids'].queryset = Student.objects.filter(branch=branch)
        else:
            self.fields['student_ids'].queryset = Student.objects.none()

    def validate_student_ids(self, students):
        branch = self._get_branch()
        if not branch:
            raise serializers.ValidationError("Failed to determine branch for student validation.")

        invalid_students = [s for s in students if s.branch_id != branch.id]
        if invalid_students:
            names = ", ".join([str(s) for s in invalid_students])
            raise serializers.ValidationError(
                f"Students ({names}) do not belong to branch {branch.name}."
            )
            
        return students

    def create(self, validated_data):
        students = validated_data.pop('student_ids', [])
        group = Group.objects.create(**validated_data)
        group.students.set(students)
        return group

    def update(self, instance, validated_data):
        students = validated_data.pop('student_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if students is not None:
            instance.students.set(students)
            
        return instance


class BranchSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='branch-detail', read_only=True)
    staff_members_input = serializers.PrimaryKeyRelatedField(
        many=True, queryset=CustomUser.objects.all(), write_only=True, source='staff_members', required=False
    )

    class Meta:
        model = Branch
        fields = ['id', 'display_name', 'url', 'name', 'address', 'city', 'status', 'staff_members_input']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'staff_members_input' in self.fields:
            self.fields['staff_members_input'].queryset = CustomUser.objects.exclude(role='admin')

    def get_display_name(self, obj):
        return f"{obj.name} (Archived)" if obj.status == 'archived' else obj.name

    def create(self, validated_data):
        staff_data = validated_data.pop('staff_members', [])
        branch = Branch.objects.create(**validated_data)
        current_user = self.context['request'].user
        BranchMember.objects.get_or_create(branch=branch, user=current_user, defaults={'role': 'branch_admin'})
        for user in staff_data:
            if user != current_user:
                role_in_branch = {'teacher': 'teacher', 'branch_admin': 'branch_admin'}.get(user.role, 'staff')
                BranchMember.objects.get_or_create(branch=branch, user=user, defaults={'role': role_in_branch})
        return branch


class BranchDetailSerializer(serializers.ModelSerializer):
    staff_members = serializers.StringRelatedField(many=True, read_only=True)

    groups_url = serializers.SerializerMethodField()
    subjects_url = serializers.SerializerMethodField()
    students_url = serializers.SerializerMethodField()
    schedule = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'address', 'city', 'status', 
            'staff_members', 'groups_url', 'subjects_url', 'students_url', 'schedule'
        ]

    def get_groups_url(self, obj):
        request = self.context.get('request')
        from rest_framework.reverse import reverse
        base_url = reverse('group-list', request=request)
        return f"{base_url}?branch={obj.id}"

    def get_subjects_url(self, obj):
        request = self.context.get('request')
        from rest_framework.reverse import reverse
        base_url = reverse('subject-list', request=request)
        return f"{base_url}?branch={obj.id}"

    def get_students_url(self, obj):
        request = self.context.get('request')
        from rest_framework.reverse import reverse
        base_url = reverse('branch-detail', kwargs={'pk': obj.id}, request=request)
        return f"{base_url}students/"

    def get_schedule(self, obj):
        user = self.context['request'].user
        lessons = Lesson.objects.filter(group__branch=obj)
        if user.role == 'teacher': 
            lessons = lessons.filter(teacher=user)
        
        child_context = self.context.copy()

        return {
            'scheduled': LessonSerializer(
                lessons.filter(status='scheduled').order_by('start_at'), 
                many=True, 
                context=child_context
            ).data,
            'completed': LessonSerializer(
                lessons.filter(status='completed').order_by('-start_at'), 
                many=True, 
                context=child_context
            ).data,
            'canceled': LessonSerializer(
                lessons.filter(status='canceled').order_by('-start_at'), 
                many=True, 
                context=child_context
            ).data,
        }


class LessonSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='lesson-detail', read_only=True)
    teacher_name = serializers.ReadOnlyField(source='teacher.get_full_name')
    group_name = serializers.ReadOnlyField(source='group.name')
    subject_name = serializers.ReadOnlyField(source='subject.name')
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'url', 'name', 'lesson_type', 'subject', 'subject_name', 
            'group', 'group_name', 'teacher', 'teacher_name', 
            'start_at', 'end_at', 'status'
        ]


class LessonActionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='lesson-detail', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ['id', 'url', 'name', 'lesson_type', 'group', 'subject', 'teacher', 'start_at', 'end_at', 'status']

    def _get_branch(self):
        if self.instance:
            if hasattr(self.instance, 'group'):
                return self.instance.group.branch
            if isinstance(self.instance, Branch):
                return self.instance
        return self.context.get('branch')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        branch = self._get_branch()
        
        if branch:
            self.fields['teacher'].queryset = CustomUser.objects.filter(
                role='teacher',
                branchmember__branch=branch,
                branchmember__role='teacher'
            ).distinct()
            self.fields['group'].queryset = Group.objects.filter(branch=branch)
            self.fields['subject'].queryset = Subject.objects.filter(branch=branch)

    def validate(self, data):
        start = data.get('start_at', self.instance.start_at if self.instance else None)
        end = data.get('end_at', self.instance.end_at if self.instance else None)
        if start and end and start >= end:
            raise serializers.ValidationError({"end_at": "End time must be later than start time."})
        return data


class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['name', 'lesson_type', 'group', 'subject', 'teacher', 'start_at', 'end_at', 'status']

    def _get_branch(self):
        return self.context.get('branch')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        branch = self._get_branch()
        
        if branch:
            self.fields['teacher'].queryset = CustomUser.objects.filter(
                role='teacher',
                branchmember__branch=branch,
                branchmember__role='teacher'
            ).distinct()
            self.fields['group'].queryset = Group.objects.filter(branch=branch)
            self.fields['subject'].queryset = Subject.objects.filter(branch=branch)
        else:
            self.fields['teacher'].queryset = CustomUser.objects.none()
            self.fields['group'].queryset = Group.objects.none()
            self.fields['subject'].queryset = Subject.objects.none()

    def validate_teacher(self, value):
        branch = self._get_branch()
        if value.role != 'teacher':
            raise serializers.ValidationError("Chosen user does not have the global teacher role.")

        if branch and not BranchMember.objects.filter(branch=branch, user=value, role='teacher').exists():
            raise serializers.ValidationError(
                f"This teacher is not registered in the branch '{branch.name}'."
            )
        return value

    def validate_status(self, value):
        if value in ['canceled', 'completed']:
            raise serializers.ValidationError(f"Lesson with this status cannot be created.")
        return value

    def validate(self, data):
        if data['start_at'] >= data['end_at']:
            raise serializers.ValidationError({
                "end_at": "End time must be later than start time."
            })

        branch = self._get_branch()
        if branch:
            if data['group'].branch_id != branch.id:
                raise serializers.ValidationError({"group": "This group does not belong to the current branch."})
            if data['subject'].branch_id != branch.id:
                raise serializers.ValidationError({"subject": "This subject does not belong to the current branch."})

        return data

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    phone = serializers.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']

    def validate(self, attrs):
        attrs[self.username_field] = attrs.get('phone')
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['role'] = user.role
        token['email'] = user.email
        
        full_name = f"{user.first_name} {user.last_name}".strip()
        token['full_name'] = full_name if full_name else user.phone

        return token