import Control from "./Control/Control";
import "./Room.css";
import RoomVideo, { type IUserData } from "./RoomVideo/RoomVideo";
import avatar1Img from "../../assets/img/avatars/avatar-boy.svg";
import avatar2Img from "../../assets/img/avatars/avatar-woman1.svg";
import avatar3Img from "../../assets/img/avatars/avatar-man2.svg";
import avatar4Img from "../../assets/img/avatars/avatar-man1.svg";

const Room = () => {
    const usersData: IUserData[] = [
        {
            username: "Tolper4161",
            avatar: avatar1Img,
            isOwner: true
        },
        {
            username: "User123",
            avatar: avatar2Img
        },
        {
            username: "Lorem Ipsum",
            avatar: avatar3Img
        },
        {
            username: "Dolor",
            avatar: avatar4Img
        }
    ];
    const title = "Tolper4161 Room";

    return (
        <section className="videochat">
            <div className="room">
                <span className="room__title">{ title }</span>
                <div className="room__content">
                    <ul className="room-video">
                        {
                            usersData.map((userData) => (
                                <li className="room-video-item">
                                    <RoomVideo
                                        username={userData.username}
                                        avatar={ userData.avatar }
                                        isOwner={userData.isOwner}
                                    />
                                </li>
                            ))
                        }
                    </ul>
                </div>
            </div>
            <Control />
        </section>
    );
};

export default Room;
