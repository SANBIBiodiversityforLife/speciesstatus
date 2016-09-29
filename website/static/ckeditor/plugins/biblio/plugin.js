CKEDITOR.plugins.add('biblio', {
    requires: 'widget',
    icons: 'biblio',
    init: function(editor) {
        
		
		// editor.addCommand('biblio', new CKEDITOR.dialogCommand('biblioDialog'));

		/*
		editor.ui.addButton( 'Biblio', {
			label: 'Insert Reference',
			command: 'biblio',
			toolbar: 'insert'
		});*/
		
		CKEDITOR.dialog.add( 'biblioDialog', this.path + 'dialogs/biblio.js' );

        editor.widgets.add( 'biblio', {
            button: 'Insert reference',
            template: '<span class="biblio" id="">Reference</span>',
            editables: {},
            allowedContent: 'span[*]',
            dialog: 'biblioDialog',
            upcast: function( element ) {
                return element.name == 'span' && element.hasClass( 'biblio' );
            },
            init: function() {
                doi = $(this.element).attr('data-doi');
                if(doi)
                    this.setData('data-doi', doi);
            },
            data: function() {
                if (this.data['data-doi']) {
                    this.setData('data-doi', this.data['data-doi']);
                    this.element.setAttribute('data-doi', this.data['data-doi']);
					
					// Set a throbber so the user knows we are doing something
					this.element.getChild(0).setAttribute('src', '/static/img/throbber.gif');
					
					// Try and get the DOI from the database
					$.ajax({url: '/biblio/get-doi/' + this.data['data-doi'],
						dataType: 'json',
						success: function(result){
							console.log('success');
							console.log(result);

							ele.setAttribute('data-aw-copyright', result.copyright);
							ele.getChild(0).setAttribute('src', result.thumbnail_preview_url);
						},
						error: function(jqXHR, textStatus, errorThrown) {
							console.log('error');
							console.log(errorThrown);
						}
					});
                };
            }
        });
    }
});