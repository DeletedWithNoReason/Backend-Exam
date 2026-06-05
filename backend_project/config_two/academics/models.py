from django.db import models
from config import settings
from django.db.models import Q

class ActiveManager(models.Manager):
    def for_user(self, user):
        qs = self.all()
        if user.role == 'admin':
            return qs
        if self.model.__name__ == 'Branch':
            return qs.filter(
                Q(branchmember__user=user, branchmember__role='branch_admin') |
                Q(branchmember__user=user, status='active')
            ).distinct()

        field_names = [f.name for f in self.model._meta.get_fields()]

        if 'branch' in field_names:
            return qs.filter(
                Q(branch__branchmember__user=user, branch__branchmember__role='branch_admin') |
                Q(branch__branchmember__user=user, status='active')
            ).distinct()
        if 'status' in field_names:
            return qs.filter(status='active')
            
        return qs

class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=100)
    objects = models.Manager()
    active = ActiveManager()
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'), ('archived', 'Archived')],
          default='active')
    staff_members = models.ManyToManyField(
        'users.CustomUser', 
        through='BranchMember', 
        related_name='branches', 
        blank=True
    )

    def __str__(self):
        return self.name
    
    @property
    def schedule(self):
        return Lesson.objects.filter(group__branch=self).order_by('start_at')
    
    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'

class BranchMember(models.Model):
    ROLE_CHOICES = [
        ('branch_admin', 'Branch Admin'),
        ('teacher', 'Teacher'),
    ]
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ('user', 'branch')

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    branch = models.ForeignKey(Branch, 
    on_delete=models.PROTECT, related_name='subjects')
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'), ('archived', 'Archived')], 
        default='active')
    
    objects = models.Manager()
    active = ActiveManager()
    
    def __str__(self):
        return f"{self.name} ({self.branch.name})"
    
    class Meta:
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    students = models.ManyToManyField('students.Student', related_name='student_groups', blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='groups')
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'), ('archived', 'Archived')],
        default='active')
    subjects = models.ManyToManyField(Subject, related_name='groups', blank=True)
    objects = models.Manager()
    active = ActiveManager()

    def __str__(self):
        return f"{self.name} - {self.branch.name}"
    
    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'

class Lesson(models.Model):
    name = models.CharField(max_length=255)
    lesson_type = models.CharField(max_length=50, choices=[
        ('group_lesson', 'Group'), ('individual', 'Individual')],
          default='group_lesson')
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name='lessons')
    students = models.ManyToManyField('students.Student', related_name='lessons')
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled')],
          default='scheduled')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='lessons'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='lessons',
    )

    def __str__(self):
        group_name = self.group.name if self.group else "No Group"
        teacher_name = self.teacher.get_full_name() if self.teacher else "No Teacher"
        return f"{group_name} - {teacher_name} on {self.start_at}"
    
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    lesson = models.ForeignKey('academics.Lesson', on_delete=models.CASCADE, related_name='attendance')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    mark = models.PositiveIntegerField(null=True, blank=True)
    commentary = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('lesson', 'student')