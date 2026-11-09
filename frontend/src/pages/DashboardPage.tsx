import './DashboardPage.css';
import './sidebar.css';
import './panel.css';
import './mobile-nav.css';
import RoomOptionsForm from '../components/RoomOptionsForm/RoomOptionsForm';

const DashboardPage = () => {
    return (
        <section className="dashboard">
            <nav className="nav ph-100">
                <div className="nav__content">
                    <div className="nav__header">
                        <a href="#" className="nav-logo-link">
                            <img
                                src="./img/logo-min.svg"
                                alt="Min Logo"
                                className="nav-logo"
                            />
                        </a>
                        <hr className="nav__line" />
                        <ul className="nav-btn-list nav-main">
                            <li className="nav-list-item btn-list-item">
                                <button className="btn-icon icon icon-home nav-btn nav-btn_active"></button>
                            </li>
                            <li className="nav-list-item btn-list-item">
                                <button className="btn-icon icon icon-videochat nav-btn"></button>
                            </li>
                        </ul>
                    </div>
                    <ul className="nav-btn-list nav-footer">
                        <li className="nav-list-item btn-list-item">
                            <button className="btn-icon icon icon-bell nav-btn"></button>
                        </li>
                        <li className="nav-list-item btn-list-item">
                            <button className="btn-icon icon icon-moon nav-btn nav-btn_active"></button>
                        </li>
                    </ul>
                </div>
            </nav>
            <div className="panel sidebar ph-100">
                <div className="panel-header sidebar__header">
                    <b className="panel-header__title">Friends List</b>
                    <button className="btn-icon icon icon-plus sidebar__add-btn"></button>
                </div>
                <div className="panel-main">
                    <ul className="friends">
                        <li className="friend">
                            <img src="./img/avatars/avatar-woman1.svg" alt="" className="friend__avatar" />
                            <span className="friend__username">User123</span>
                        </li>
                        <li className="friend">
                            <img src="./img/avatars/avatar-man2.svg" alt="" className="friend__avatar" />
                            <span className="friend__username">Lorem Ipsum</span>
                        </li>
                        <li className="friend">
                            <img src="./img/avatars/avatar-man1.svg" alt="" className="friend__avatar" />
                            <span className="friend__username">Dolor</span>
                        </li>
                    </ul>
                </div>
                <div className="panel-footer">
                    <div className="account">
                        <div className="account__info">
                            <img src="./img/avatars/avatar-boy.svg" alt="" className="account__avatar" />
                            <b className="account__username">Username</b>
                        </div>
                        <button className="btn-icon icon icon-wheel account__btn"></button>
                    </div>
                </div>
            </div>
            <div className="options" id="options">
                <div className="panel">
                    <div className="panel-header">
                        <b className="panel-header__title">My Room</b>
                    </div>
                    <div className="panel-main">
                        <div className="room-options">
                            <div className="room-options__left">
                                <RoomOptionsForm className="room-options__form" />
                                <div className="room-options__btns">
                                    <button className="btn icon icon-phone green-bg room-options-btn">Start Call</button>
                                    <button className="btn icon icon-link blue-bg room-options-btn">Copy Invite Link</button>
                                </div>
                            </div>
                            <div className="room-options__right">
                                <img src="./img/qr-code.svg" alt="" className="room-options__qr" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default DashboardPage;
