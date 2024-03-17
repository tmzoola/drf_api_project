from django.core.validators import FileExtensionValidator, MaxLengthValidator
from django.db import models
from django.db.models import UniqueConstraint

from users.models import User
from shared.models import BaseModel


class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(
        upload_to='post_images/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpeg', 'jpg', 'png', 'heic', 'heif']),
        ]
    )
    caption = models.TextField(validators=[MaxLengthValidator(2000)])


    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'


class PostComment(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(validators=[MaxLengthValidator(2000)])
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               related_name='child',
                               null=True,
                               blank=True
                               )

class PostLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')


    class Meta:
        constraint = [
            UniqueConstraint(
                fields=['author','post'],
            )
        ]
class CommentLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        constraint = [
            UniqueConstraint(
                fields=['author','comment'],
            )
        ]