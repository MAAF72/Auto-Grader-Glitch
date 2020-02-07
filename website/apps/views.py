import uuid
from os import path, remove
from time import sleep
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Sum, Max
from django.contrib.auth.models import User
import django.contrib.auth as auth
from . import models, forms

TC_IN_PATH = path.join('..', 'judge', 'TCIn')
TC_OUT_PATH = path.join('..', 'judge', 'TCOut')
SUBMISSION_PATH = path.join('..', 'judge', 'Submission')

def delete_file(file):
    '''
    Delete the file if exist
    '''
    for _ in range(10):
        print('deleting', file)
        try:
            if path.isfile(file):
                remove(file)
        except OSError as error:
            sleep(5)
            print('Delete failed, retrying...', error)
        except Exception as error:
            sleep(5)
            print('Delete failed, retrying...', error)
        else:
            break

def get_file_content(file_name, extension):
    content = ''
    with open('{}.{}'.format(file_name, extension), 'r') as file:
        content = file.read()
    return content

@staff_member_required(login_url='apps:index')
def problem_create(request):
    if request.method == 'POST':
        form = forms.ProblemForm(request.POST)
        if form.is_valid():
            return redirect('apps:problem', form.save().pk)
    else:
        form = forms.ProblemForm()
        context = {
            'form': form,
            'title': 'Create new problem',
            'button': 'Create',
        }
    return render(request, 'apps/problem_create_or_edit.html', context)

@staff_member_required(login_url='apps:index')
def problem_edit(request, id):
    if request.method == 'POST':
        form = forms.ProblemForm(request.POST, instance=models.Problem.objects.get(id=id))
        if form.is_valid():
            return redirect('apps:problem', form.save().pk)
    else:
        form = forms.ProblemForm(instance=models.Problem.objects.get(id=id))
        context = {
            'form': form,
            'title': 'Edit {}'.format(form.instance.name),
            'button': 'Save',
        }
    return render(request, 'apps/problem_create_or_edit.html', context)

@staff_member_required(login_url='apps:index')
def problem_delete(request, id):
    models.Problem.objects.get(id=id).delete()
    return redirect('apps:problems_manage')

@staff_member_required(login_url='apps:index')
def problem_test_case(request, id):
    test_cases = models.TestCase.objects.filter(problem__id=id)
    problem_name = models.Problem.objects.get(id=id).name
    context = {
        'title': 'ULTRAG - {}\'s Test Case'.format(problem_name),
        'test_cases': test_cases,
        'problem_id': id,
        'problem_name': problem_name
    }
    return render(request, 'apps/problem_test_case.html', context)

@staff_member_required(login_url='apps:index')
def test_case_create(request, id):
    if request.method == 'POST':
        file_name = str(uuid.uuid4())
        form = forms.TestCaseForm(request.POST)

        if form.is_valid():
            form.input = file_name
            form.output = file_name
            form.problem = models.Problem.objects.get(id=id)
            form.save(request.POST['input_content'], request.POST['output_content'])
            return redirect('apps:problem_test_case', id)
    else:
        form = forms.TestCaseForm()
        problem_name = models.Problem.objects.get(id=id).name
        context = {
            'form': form,
            'title': 'Create new test case',
            'button': 'Create',
            'problem_name': problem_name
        }
        return render(request, 'apps/test_case_create_or_edit.html', context)

@staff_member_required(login_url='apps:index')
def test_case_edit(request, id):
    if request.method == 'POST':
        form = forms.TestCaseForm(request.POST, instance=models.TestCase.objects.get(id=id))
        if form.is_valid():
            form.save(request.POST['input_content'], request.POST['output_content'])
            return redirect('apps:problem_test_case', form.instance.problem.id)
    else:
        form = forms.TestCaseForm(instance=models.TestCase.objects.get(id=id))
        input_content = get_file_content(path.join(TC_IN_PATH, form.instance.input.name), 'txt')
        output_content = get_file_content(path.join(TC_OUT_PATH, form.instance.output.name), 'txt')
        context = {
            'form': form,
            'title': 'Edit {}'.format(form.instance.name),
            'button': 'Save',
            'problem_name': form.instance.problem.name,
            'input_content': input_content,
            'output_content': output_content,
        }
        return render(request, 'apps/test_case_create_or_edit.html', context)

@staff_member_required(login_url='apps:index')
def test_case_delete(request, id):
    test_case = models.TestCase.objects.get(id=id)
    problem_id = test_case.problem.id
    #delete file
    delete_file('{}.txt'.format(path.join(TC_IN_PATH, test_case.input.name)))
    delete_file('{}.txt'.format(path.join(TC_OUT_PATH, test_case.output.name)))
    test_case.delete()
    return redirect('apps:problem_test_case', problem_id)

def send_submission(args):
    import pika
    from json import dumps

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )

    channel = connection.channel()
    channel.queue_declare(queue='submission', durable=True)

    message = [args[0], args[1], args[2], args[3], args[4], args[5], args[6]]
    channel.basic_publish(
        exchange='',
        routing_key='submission',
        body=dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    print('send', message)
    connection.close()

def index(request):
    context = {
        'title': 'ULTRAG - Index'
    }
    return render(request, 'apps/index.html', context)

def login(request):
    context = {
        'title': 'ULTRAG - Login',
        'message': '',
    }

    if request.user.is_authenticated:
        return redirect('apps:index')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(request, username=username, password=password)
        if not user:
            context['message'] = 'Wrong Credential!'
        else:
            auth.login(request, user)
            return redirect('apps:index')
    return render(request, 'apps/login.html', context)

def register(request):
    context = {
        'title': 'ULTRAG - Register',
        'message': '',
    }

    if request.user.is_authenticated:
        return redirect('apps:index')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        if not User.objects.filter(~Q(username__iexact=username), ~Q(email__iexact=email)).exists():
            context['message'] = 'Username or Email Has Already Been Taken!'
        else:
            User.objects.create_user(username=username, email=email, password=password).save()
            user = auth.authenticate(request, username=username, password=password)
            auth.login(request, user)

            return redirect('apps:index')
    return render(request, 'apps/register.html', context)

def logout(request):
    auth.logout(request)
    return redirect('apps:index')

def profile(request, username):
    user = User.objects.get(username=username)
    submissions = models.Submission.objects.filter(user=user)
    user.score = (
        submissions
        .values('problem')
        .annotate(greatest=Max('score'))
        .aggregate(total=Sum('greatest'))['total']
    )

    context = {
        'title': 'ULTRAG - {}\'s Profile'.format(username),
        'user': user,
        'submissions': submissions
    }
    return render(request, 'apps/profile.html', context)

def submissions(request):
    submissions = models.Submission.objects.all().order_by('-date')

    context = {
        'title': 'ULTRAG - Submission List',
        'submissions': submissions
    }
    return render(request, 'apps/submissions.html', context)

def submission(request, id):
    submission = models.Submission.objects.get(id=id)
    EXTENSION = {
        'GO': 'go',
        'C++': 'cpp',
        'C': 'c'
    }

    submission.code = 'You cannot view this submission\'s code'
    if request.user == submission.user:
        submission.code = get_file_content(
            path.join(SUBMISSION_PATH, submission.file.name),
            EXTENSION[submission.language]
        )

    context = {
        'submission': submission
    }
    return render(request, 'apps/submission.html', context)

def problems(request):
    problems = models.Problem.objects.all()

    for problem in problems:
        problem.total = models.Submission.objects.filter(Q(problem_id=problem), ~Q(status='PEN'))
        problem.success = 0.00
        if problem.total.count() > 0:
            problem.success = round(problem.total.filter(status='AC').count() / problem.total.count() * 100.0, 2)

        problem.total = problem.total.count()

    context = {
        'title': 'ULTRAG - Problem List',
        'problems': problems
    }
    return render(request, 'apps/problems.html', context)

@staff_member_required(login_url='apps:index')
def problems_manage(request):
    problems = models.Problem.objects.all()
    for problem in problems:
        problem.test_cases = models.TestCase.objects.filter(problem=problem).count()
        problem.submissions = models.Submission.objects.filter(
            Q(problem_id=problem),
            ~Q(status='PEN')
        )
        problem.success = 0.00
        if problem.submissions.count() > 0:
            problem.success = round(problem.submissions.filter(status='AC').count() / problem.submissions.count() * 100.0, 2)

        problem.submissions = problem.submissions.count()

    context = {
        'title': 'ULTRAG - Manage Problems',
        'problems': problems
    }
    return render(request, 'apps/problems_manage.html', context)

def problem(request, id):
    if request.method == 'POST' and request.user.is_authenticated:
        if request.FILES['submission'].size <= 256 * 1024:
            extension = str(request.FILES['submission']).lower().rsplit('.', 1)[-1]
            LANGUAGE = {
                'go': 'GO',
                'cpp': 'C++',
                'c': 'C'
            }

            if extension in LANGUAGE:
                submission = models.Submission.objects.create(
                    user=request.user,
                    problem=models.Problem.objects.get(id=id),
                    language=LANGUAGE[extension],
                    host=0
                )
                file_name = str(uuid.uuid4())
                with open('{}.{}'.format(path.join(SUBMISSION_PATH, file_name), extension), 'wb+') as file:
                    #check if file.read() contain malicious code
                    for chunk in request.FILES['submission']:
                        file.write(chunk)
                    submission.file = file_name
                    submission.save()

                #id, problem, file, language, time_limit, memory_limit, test_case
                send_submission([
                    submission.id,
                    submission.problem.id,
                    file_name,
                    submission.language,
                    submission.problem.time_limit,
                    submission.problem.memory_limit,
                    [(tc.input.name, tc.output.name) for tc in models.TestCase.objects.filter(problem=submission.problem)],
                ])
                return redirect('apps:submission', submission.id)
            return redirect('') #Extension not allowed
        return redirect('') #File Size Limit Exceeded
    else:
        problem = models.Problem.objects.get(id=id)
        samples = models.TestCase.objects.filter(problem=problem, sample=True) #join
        for sample in samples:
            sample.input = get_file_content(path.join(TC_IN_PATH, sample.input.name), 'txt')
            sample.output = get_file_content(path.join(TC_OUT_PATH, sample.output.name), 'txt')

        context = {
            'title': 'ULTRAG - {}'.format(problem.name),
            'problem': problem,
            'samples': samples,
        }
        return render(request, 'apps/problem.html', context)
