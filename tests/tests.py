from django.test import TestCase
from django.contrib.auth.models import User

from cacheops import invalidate_all
from .models import Category, Post, Extra, Profile


class BaseTestCase(TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        invalidate_all()


class BasicTests(BaseTestCase):
    fixtures = ['basic']

    def test_it_works(self):
        with self.assertNumQueries(1):
            cnt1 = Category.objects.cache().count()
            cnt2 = Category.objects.cache().count()
            self.assertEqual(cnt1, cnt2)

    def test_invalidation(self):
        post = Post.objects.cache().get(pk=1)
        post.title += ' changed'
        post.save()

        with self.assertNumQueries(1):
            changed_post = Post.objects.cache().get(pk=1)
            self.assertEqual(post.title, changed_post.title)

    def test_invalidate_by_foreign_key(self):
        posts = list(Post.objects.cache().filter(category=1))
        Post.objects.create(title='New Post', category_id=1)

        with self.assertNumQueries(1):
            changed_posts = list(Post.objects.cache().filter(category=1))
            self.assertEqual(len(changed_posts), len(posts) + 1)

    def test_invalidate_by_one_to_one(self):
        extras = list(Extra.objects.cache().filter(post=3))
        Extra.objects.create(post_id=3, tag=0)

        with self.assertNumQueries(1):
            changed_extras = list(Extra.objects.cache().filter(post=3))
            self.assertEqual(len(changed_extras), len(extras) + 1)

    def test_invalidate_by_boolean(self):
        count = Post.objects.cache().filter(visible=True).count()

        post = Post.objects.get(pk=1, visible=True)
        post.visible = False
        post.save()

        with self.assertNumQueries(1):
            new_count = Post.objects.cache().filter(visible=True).count()
            self.assertEqual(new_count, count - 1)

    def test_db_column(self):
        e = Extra.objects.cache().get(tag=5)
        e.save()

    def test_fk_to_db_column(self):
        e = Extra.objects.cache().get(to_tag__tag=5)
        e.save()

        with self.assertNumQueries(1):
            Extra.objects.cache().get(to_tag=5)


class ContribTests(BaseTestCase):
    def setUp(self):
        user = User.objects.create(username='Suor')
        Profile.objects.create(pk=2, user=user, tag=10)
        super(ContribTests, self).setUp()

    def test_16(self):
        p = Profile.objects.cache().get(user__id__exact=1)
        p.save()

        with self.assertNumQueries(1):
            Profile.objects.cache().get(user=1)
