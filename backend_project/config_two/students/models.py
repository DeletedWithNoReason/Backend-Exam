from django.db import models
from academics.models import ActiveManager

class Parent_GuardianData(models.Model):
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=255, blank=True)

    def __str__(self):
        return self.name or "Unnamed Guardian"

    class Meta:
        verbose_name = "Parent/Guardian Data"
        verbose_name_plural = "Parent/Guardian Data"

class Student(models.Model):
    id = models.AutoField(unique=True, primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255)
    
    parents = models.ManyToManyField(
        Parent_GuardianData, 
        blank=True, 
        related_name='students',
        verbose_name="Parents / Guardians"
    )
    
    status = models.CharField(
        max_length=20, 
        choices=[('active', 'Active'), ('archived', 'Archived')], 
        default='active'
    )
    
    branch = models.ForeignKey(
        'academics.Branch', 
        on_delete=models.PROTECT, 
        related_name='students'
    )

    objects = models.Manager()
    active = ActiveManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Enrollment(models.Model):
    subject = models.ForeignKey(
        'academics.Subject',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    term = models.CharField(max_length=255, blank=True, default='No term specified')

    class Meta:
        unique_together = ['student', 'subject']
        
    def __str__(self):
        return f"{self.student} → {self.subject} ({self.term})"