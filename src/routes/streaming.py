# src/routes/streaming.py
from flask import Blueprint, Response, request, current_app
from src.streaming.generators import video_stream_generator, camera_stream_generator

streaming_bp = Blueprint('streaming', __name__)

@streaming_bp.route('/camera_feed')
def camera_feed():
    """カメラからのM-JPEGストリームを配信するエンドポイント"""
    camera_index = request.args.get('camera_index', 0, type=int)
    stop_event = current_app.state.background_thread_stop_event
    return Response(camera_stream_generator(camera_index, stop_event),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@streaming_bp.route('/video_feed')
def video_feed():
    """M-JPEGストリームを配信するエンドポイント"""
    window_title = request.args.get('window_title', '')
    if not window_title:
        return Response("Error: window_title is required.", status=400)
    
    stop_event = current_app.state.background_thread_stop_event
    return Response(video_stream_generator(window_title, stop_event),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
