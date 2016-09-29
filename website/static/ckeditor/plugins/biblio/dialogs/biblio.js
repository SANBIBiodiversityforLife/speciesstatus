CKEDITOR.dialog.add( 'biblioDialog', function( editor ) {
    return {
        title: 'Insert a reference',
        minWidth: 400,
        minHeight: 100,

        contents: [
            {
                id: 'biblio',
                elements: [
                    {
                        id: 'data-doi',
                        type: 'text',
                        label: 'Select a reference by inserting a DOI',
                        setup: function( widget ) {
                            this.setValue( widget.data['data-doi'] );
                        },
                        commit: function( widget ) {
                            widget.setData( 'data-doi', this.getValue() );
                        },
                    },
                ]
            },
        ]
    };
});