import "./Sidebar.css";

import avatarImg from "../../assets/img/avatars/avatar-boy.svg";
import avatar1Img from "../../assets/img/avatars/avatar-woman1.svg";
import avatar2Img from "../../assets/img/avatars/avatar-man2.svg";
import avatar3Img from "../../assets/img/avatars/avatar-man1.svg";

import FriendsList from "../FriendsList/FriendsList";
import type { FriendItemProps } from "../FriendsList/FriendItem";
import Account from "../Account/Account";

const Sidebar = () => {
    const friendsList : FriendItemProps[] = [
        {
            avatar: avatar1Img,
            username: "User123"
        },
        {
            avatar: avatar2Img,
            username: "Lorem Ipsum"
        },
        {
            avatar: avatar3Img,
            username: "Dolor"
        }
    ];

    return (
        <div className="panel sidebar ph-100">
            <div className="panel-header sidebar__header">
                <b className="panel-header__title">Friends List</b>
                <button className="btn-icon icon icon-plus sidebar__add-btn"></button>
            </div>
            <div className="panel-main">
                <FriendsList data={ friendsList } />
            </div>
            <div className="panel-footer">
                <Account avatarImg={ avatarImg } username={ "Tolper4161" } />
            </div>
        </div>
    );
};

export default Sidebar;
