from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from .models import Blog, BlogType
from read_statistics.utils import read_statistics_once_read
# from user.forms import LoginForm
# 并入主页的views.py所需要的包
import datetime
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache
from django.urls import reverse
from read_statistics.utils import get_seven_days_read_data, get_today_hot_data, get_yesterday_hot_data

def get_blog_list_common_data(blogs_all_list, request):
    paginator = Paginator(blogs_all_list, settings.EACH_PAGE_BLOGS_NUMBER)  # 每7篇进行分页
    page_num = request.GET.get('page', 1)  # 获取url的页面参数 （GET请求）如果没有page的值则返回1
    page_of_blogs = paginator.get_page(page_num)  # 获取某一页的数据
    current_page_num = page_of_blogs.number  # 获取当前页码
    # 获取当前页面前后两页页码
    page_range = list(range(max(current_page_num - 2, 1), current_page_num)) + \
                 list(range(current_page_num, min(current_page_num + 2, paginator.num_pages) + 1))
    # 加上省略页码标记
    if page_range[0] - 1 >= 2:
        page_range.insert(0, '...')
    if paginator.num_pages - page_range[-1] >= 2:
        page_range.append('...')
    # 加上第一页和最后一页
    if page_range[0] != 1:
        page_range.insert(0, 1)
    if page_range[-1] != paginator.num_pages:
        page_range.append(paginator.num_pages)

    # 获取日期对应的文章数量
    blog_dates = Blog.objects.dates('created_time', 'month', order="DESC")  # 通过created_time字段返回所有时间值中非重复的年／月列表
    blog_dates_dic = {}
    for blog_date in blog_dates:
        blog_count = Blog.objects.filter(created_time__year=blog_date.year, created_time__month=blog_date.month).count()
        blog_dates_dic[blog_date] = blog_count

    context = {}
    # context['blogs'] = page_of_blogs.object_list
    context['page_of_blogs'] = page_of_blogs
    context['page_range'] = page_range
    context['blog_types'] = BlogType.objects.all()
    context['blog_types_menu'] = context['blog_types']
    context['blog_dates'] = blog_dates_dic

    return context


def blog_list(request):
    blogs_all_list = Blog.objects.all()

    context = get_blog_list_common_data(blogs_all_list, request)
    # 并入主页数据
    home(context)
    return render(request, 'blog/blog_list.html', context)

def blogs_with_type(request, blog_type_pk):
    blog_type = get_object_or_404(BlogType, pk=blog_type_pk)
    blogs_all_list = Blog.objects.filter(blog_type=blog_type)

    context = get_blog_list_common_data(blogs_all_list, request)
    context['blog_type'] = blog_type

    return render(request, 'blog/blogs_with_type.html', context)

def blogs_with_date(request, year, month):
    blogs_all_list = Blog.objects.filter(created_time__year=year, created_time__month=month)

    context = get_blog_list_common_data(blogs_all_list, request)
    context['blogs_with_date'] = '{}年{}月'.format(year, month)

    return render(request, 'blog/blogs_with_date.html', context)

def blog_detail(request, blog_pk):
    # 由前端提供的数据最好使用get_object_or_404
    blog = get_object_or_404(Blog, pk=blog_pk)
    read_cookie_key = read_statistics_once_read(request, blog)

    context = {}
    context['previous_blog'] = Blog.objects.filter(created_time__gt=blog.created_time).last()
    context['next_blog'] = Blog.objects.filter(created_time__lt=blog.created_time).first()
    context['blog'] = blog
    context['blog_types_menu'] = BlogType.objects.all()
    # context['login_form'] = LoginForm()
    response = render(request, 'blog/blog_detail.html', context)  # 响应
    response.set_cookie(read_cookie_key.format(blog_pk), 'true')  # 阅读cookie标记

    return response


# 并入主页的试图函数
def get_7_days_hot_blogs():
    today = timezone.now().date()
    date = today - datetime.timedelta(days=7)
    blogs = Blog.objects \
                .filter(read_details__date__lt=today, read_details__date__gte=date) \
                .values('id', 'title') \
                .annotate(read_num_sum=Sum('read_details__read_num')) \
                .order_by('-read_num_sum')
    return blogs[:7]

def set_or_get_data_cache(data_name, func, blog_content_type):
    data = cache.get(data_name)
    if data is None:
        data = func() if blog_content_type is None else func(blog_content_type)
        cache.set(data_name, data, 3600)  # 60秒 * 60分钟 == 1h
    return data

def home(context):
    blog_content_type = ContentType.objects.get_for_model(Blog)
    # 获取7天热门数据的缓存数据
    dates_and_read_nums = set_or_get_data_cache('dates_and_read_nums', get_seven_days_read_data, blog_content_type)
    # 获取昨天热门文章的缓存数据
    hot_blogs_for_yesterday_day = set_or_get_data_cache('hot_blogs_for_yesterday_day', get_yesterday_hot_data, blog_content_type)
    # 获取7天热门文章的缓存数据
    hot_blogs_for_7_days = set_or_get_data_cache('hot_blogs_for_7_days', get_7_days_hot_blogs, None)
    context['dates'] = dates_and_read_nums['dates']
    context['read_nums'] = dates_and_read_nums['read_nums']
    context['today_hot_data'] = get_today_hot_data(blog_content_type)
    context['yesterday_hot_data'] = hot_blogs_for_yesterday_day
    context['hot_blogs_for_7_days'] = hot_blogs_for_7_days
