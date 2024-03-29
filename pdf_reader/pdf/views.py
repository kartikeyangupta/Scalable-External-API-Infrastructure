from django.http import HttpResponse, HttpResponseRedirect,  HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, get_list_or_404
from .models import PDF_File, File_Content
from .forms import PDFFileForm
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from .tasks import upload_pdf_to_s3

def index(request):
    pdf_files = PDF_File.objects.all()
    return render(request, "pdf/index.html", {'data': pdf_files})

def uploadpdf(request):
    form = PDFFileForm(request.POST, request.FILES)
    if request.method == "POST":        
        if form.is_valid():
            pdf_file = request.FILES['file_name']
            if pdf_file.name == '' or pdf_file.name.split('.')[1].lower() != 'pdf':
                return  HttpResponseBadRequest('Wrong file provided, should be only PDFs')
            file_name = pdf_file.name.split('.')[0]
            file_model = PDF_File(name=file_name)
            file_model.save()
            with open(f'{settings.FILE_LOCATION}/{file_name}-{file_model.timestamp}.pdf', "wb+") as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)
            upload_pdf_to_s3.delay(file_model.name, file_model.timestamp)
            return HttpResponseRedirect('/pdf')
        else:
            form = PDF_File()
    return render(request, "pdf/upload.html", {"form": form})

def view_pdf_content(request, file_id):
    try:
        file_name = None
        file_name = PDF_File.objects.get(pk=file_id)
        pdf_file = File_Content.objects.get(file_name_id=file_id)
        return render(request, "pdf/content.html", {'content': pdf_file.content, 'name': file_name})
    except ObjectDoesNotExist:
        if file_name:
            msg = "Lets give it retry after some time, your file is being processed by our servers."
            return render(request, "pdf/content.html", {'content': msg, 'name': file_name})
        else:
            msg = f'The File id {file_id} doesnt exist on our server.'
            return render(request, "pdf/content.html", {'content': msg, 'name': 'Incorrect PDF File ID'})
    
       

