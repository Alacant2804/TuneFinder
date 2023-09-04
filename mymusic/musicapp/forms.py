from django import forms

class ArtistTrackInputForm(forms.Form):
    artist_name = forms.CharField(label='Artist Name', max_length=100)
    track_name = forms.CharField(label='Track Name', max_length=100, required=False)  # It's optional to fill in the track name


    def clean_artist_name(self):
        artist_name = self.cleaned_data['artist_name']
        if artist_name.isdigit():
            raise forms.ValidationError("Please enter a valid artist name, not just numbers.")
        return artist_name
