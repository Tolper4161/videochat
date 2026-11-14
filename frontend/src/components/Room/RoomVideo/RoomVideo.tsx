export interface IUserData {
    username: string,
    avatar: string,
    isOwner?: boolean
}

const RoomVideo = ({ username, avatar, isOwner=false }: IUserData) => {
    return (
        <div className="room-video-window">
            <div className="room-video-window__wrap">
                <img src={ avatar } className="room-video-window__avatar" />
            </div>
            <div className="room-video-window__info">
                <span className="icon icon-microphone-mute-gray room-video-item__username">
                    { username }
                </span>
            </div>
        </div>
    );
};

export default RoomVideo;
